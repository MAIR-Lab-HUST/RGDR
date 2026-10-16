"""Redistribute an existing teaser's motion over a slower, steadier timeline.

This only resamples frames from an existing video. It does not generate images
or change the real keyframe files used by the webpage.
"""

from io import BytesIO
import math
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageFilter


def _read_exact(stream, size):
    chunks = bytearray()
    while len(chunks) < size:
        chunk = stream.read(size - len(chunks))
        if not chunk:
            raise RuntimeError("Video decoding ended before the requested frame.")
        chunks.extend(chunk)
    return bytes(chunks)


def _stats(values):
    values = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(values.mean()) if values.size else 0.0,
        "median": float(np.median(values)) if values.size else 0.0,
        "maximum": float(values.max()) if values.size else 0.0,
        "coefficient_of_variation": (
            float(values.std() / values.mean()) if values.size and values.mean() else 0.0
        ),
    }


def _rms(left, right):
    difference = right.astype(np.float32) - left.astype(np.float32)
    return float(np.sqrt(np.mean(difference * difference)))


def _blend_array(frames, position):
    left = int(math.floor(position))
    right = min(left + 1, len(frames) - 1)
    amount = position - left
    if amount < 1e-9:
        return frames[left]
    return frames[left].astype(np.float32) * (1.0 - amount) + frames[right] * amount


def _video_dimensions(source, ffmpeg):
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-threads", "2",
               "-i", str(source), "-frames:v", "1", "-f", "image2pipe",
               "-c:v", "png", "-threads", "2", "pipe:1"]
    decoded = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             check=True)
    with Image.open(BytesIO(decoded.stdout)) as image:
        return image.size


def _motion_map(source, start, end, ffmpeg, fps, width, height, motion_frames):
    low_width = 160
    low_height = max(1, round(height * low_width / width))
    frame_limit = int(math.ceil(end * fps - 1e-9)) + 1
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-threads", "2",
               "-i", str(source), "-an", "-vf",
               f"fps={fps},scale={low_width}:{low_height}:flags=area",
               "-frames:v", str(frame_limit), "-filter_threads", "1",
               "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
    decoded = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             check=True)
    size = low_width * low_height * 3
    if len(decoded.stdout) % size or len(decoded.stdout) < frame_limit * size:
        raise ValueError("The last anchor lies beyond the decodable video timeline.")
    frames = np.frombuffer(decoded.stdout, dtype=np.uint8).reshape(
        -1, low_height, low_width, 3).copy()
    # Light smoothing discounts single-pixel compression noise without imposing a
    # fixed motion threshold that could discard subtle scientific-diagram changes.
    for index in range(len(frames)):
        frames[index] = np.asarray(Image.fromarray(frames[index]).filter(
            ImageFilter.GaussianBlur(1.0)))

    interior = np.arange(math.floor(start * fps) + 1, math.ceil(end * fps)) / fps
    times = np.concatenate(([start], interior, [end]))
    positions = times * fps
    distances = []
    previous = _blend_array(frames, positions[0])
    for position in positions[1:]:
        current = _blend_array(frames, position)
        distances.append(_rms(previous, current))
        previous = current
    distances = np.asarray(distances)
    static = bool(distances.max(initial=0.0) <= 1e-8)
    if static:
        progress = (times - start) / (end - start)
    else:
        median = float(np.median(distances))
        if median <= 1e-8:
            median = float(np.median(distances[distances > 1e-8]))
        # A small, clip-relative time component keeps the inverse continuous.
        # Nearly static stretches get less screen time; larger changes get more.
        weights = 0.9 * distances + 0.1 * median
        cumulative = np.concatenate(([0.0], np.cumsum(weights)))
        progress = cumulative / cumulative[-1]
    output_progress = np.linspace(0.0, 1.0, motion_frames)
    source_times = np.interp(output_progress, progress, times)
    source_times[0], source_times[-1] = start, end

    after_distances = []
    previous = _blend_array(frames, source_times[0] * fps)
    for time in source_times[1:]:
        current = _blend_array(frames, time * fps)
        after_distances.append(_rms(previous, current))
        previous = current
    diagnostics = {"static_fallback": static, "analysis_size": [low_width, low_height],
                   "source_motion_samples": len(times),
                   "source_frame_change": _stats(distances),
                   "output_frame_change": _stats(after_distances)}
    return source_times, times, progress, diagnostics


def retime_video(source, destination, anchor_times, ffmpeg, *, fps=30,
                 motion_seconds=12.0, lead_frames=3, tail_frames=8):
    """Write a steadily changing video and return its new keyframe timestamps.

    ``anchor_times`` are increasing timestamps in the source video. Only the
    interval between its first and last entries contributes to the motion map;
    the source's opening and closing holds are excluded. The destination must
    differ from the source and is atomically replaced only after encoding passes.
    All returned timestamps are seconds. Diagnostic distances are RGB RMS values
    on lightly blurred, 160-pixel-wide analysis frames, in the range 0 to 255.
    """
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different paths.")
    if not source.is_file():
        raise FileNotFoundError(source)
    anchors = np.asarray(tuple(anchor_times), dtype=np.float64)
    if (anchors.ndim != 1 or len(anchors) < 2 or not np.isfinite(anchors).all()
            or anchors[0] < 0.0 or not (np.diff(anchors) > 0).all()):
        raise ValueError("anchor_times must contain at least two increasing finite times.")
    if not math.isfinite(fps) or fps <= 0 or not math.isfinite(motion_seconds) or motion_seconds <= 0:
        raise ValueError("fps and motion_seconds must be finite and positive.")
    if any(isinstance(n, bool) or not isinstance(n, int) or n < 0
           for n in (lead_frames, tail_frames)):
        raise ValueError("lead_frames and tail_frames must be nonnegative integers.")
    motion_frames = int(round(motion_seconds * fps)) + 1
    if motion_frames < 2:
        raise ValueError("motion_seconds must span at least one output frame.")
    width, height = _video_dimensions(source, ffmpeg)
    if width % 2 or height % 2:
        raise ValueError("H264 yuv420p output requires even source dimensions.")
    start, end = float(anchors[0]), float(anchors[-1])
    source_times, analysis_times, progress, diagnostics = _motion_map(
        source, start, end, ffmpeg, fps, width, height, motion_frames)
    motion_span = (motion_frames - 1) / fps
    mapped_anchors = lead_frames / fps + np.interp(anchors, analysis_times, progress) * motion_span
    count = lead_frames + motion_frames + tail_frames
    result = {"duration": count / fps, "anchor_times": mapped_anchors.tolist(),
              "frame_count": count, "motion_frames": motion_frames, "fps": fps,
              "size": [width, height], "source_interval": [start, end],
              "diagnostics": diagnostics}

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.NamedTemporaryFile(prefix=f".{destination.stem}-", suffix=".mp4",
                                            dir=destination.parent, delete=False)
    temporary_path = Path(temporary.name)
    temporary.close()
    decoder = encoder = None
    try:
        with tempfile.TemporaryFile() as decode_errors, tempfile.TemporaryFile() as encode_errors:
            limit = int(math.ceil(end * fps - 1e-9)) + 1
            decoder = subprocess.Popen(
                [ffmpeg, "-hide_banner", "-loglevel", "error", "-threads", "2",
                 "-i", str(source), "-an", "-vf", f"fps={fps}", "-frames:v", str(limit),
                 "-filter_threads", "1", "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"],
                stdout=subprocess.PIPE, stderr=decode_errors)
            encoder = subprocess.Popen(
                [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                 "-pix_fmt", "rgb24", "-s:v", f"{width}x{height}", "-framerate", str(fps),
                 "-i", "pipe:0", "-an", "-c:v", "libx264", "-crf", "17",
                 "-preset", "fast", "-threads", "2", "-filter_threads", "1",
                 "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temporary_path)],
                stdin=subprocess.PIPE, stderr=encode_errors)
            previous = current = None
            current_index = -1
            for output_index, source_time in enumerate(source_times):
                position = float(source_time * fps)
                nearest = round(position)
                if abs(position - nearest) < 1e-8:
                    position = float(nearest)
                right_index = int(math.ceil(position))
                while current_index < right_index:
                    previous, current = current, Image.frombytes(
                        "RGB", (width, height), _read_exact(decoder.stdout, width * height * 3))
                    current_index += 1
                if position == right_index:
                    frame = current
                else:
                    frame = Image.blend(previous, current, position - math.floor(position))
                encoded = frame.tobytes()
                if output_index == 0:
                    for _ in range(lead_frames):
                        encoder.stdin.write(encoded)
                encoder.stdin.write(encoded)
            for _ in range(tail_frames):
                encoder.stdin.write(encoded)
            encoder.stdin.close()
            decoder.stdout.close()
            decode_status, encode_status = decoder.wait(), encoder.wait()
            if decode_status or encode_status or not temporary_path.stat().st_size:
                decode_errors.seek(0)
                encode_errors.seek(0)
                raise RuntimeError("Video retiming failed: " +
                                   decode_errors.read().decode(errors="replace") +
                                   encode_errors.read().decode(errors="replace"))
        temporary_path.replace(destination)
        return result
    finally:
        for process in (decoder, encoder):
            if process is not None:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                for stream in (process.stdin, process.stdout):
                    if stream is not None and not stream.closed:
                        stream.close()
        temporary_path.unlink(missing_ok=True)
