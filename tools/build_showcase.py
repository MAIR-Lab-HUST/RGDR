"""Build an interpolated teaser from saved RGDR outputs.

Requires Pillow, NumPy and FFmpeg. The input library is supplied at build time;
published metadata contains only display text, sampled strengths and assets.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image

from retime_showcase import retime_video

CASES = [
    dict(id="human", category="Human", title="Show the bride riding a bicycle through the golden field.",
         goal="Show the bride riding a bicycle through the golden field.",
         directory="01_人物图像/P02_金色田野中的骑车新娘", endpoint=5,
         asset_prefix="bride_"),
    dict(id="open", category="Open", title="Conceal the bridge deck and lower towers beneath dense fog.",
         goal="Conceal the bridge deck and lower towers beneath dense fog.",
         directory="02_开放图像/O03_浓雾中的金门大桥", endpoint=8),
    dict(id="text", category="Text", title="Render the subtitle “Lament of Innocence” clearly and with correct spelling.",
         goal='Render the subtitle “Lament of Innocence” clearly and with correct spelling.',
         directory="04_图文结合/T05_恶魔城游戏封面", endpoint=4),
    dict(id="scientific", category="Scientific", title="Turn the horizontal red and blue excitation arrows upward.",
         goal="Turn the horizontal red and blue excitation arrows upward.",
         task_id="instruction_following_ScientificLaw_ScientificProcess_047",
         query_model="FLUX", endpoint=2, asset_prefix="excitation_"),
]



def source_images(case, library):
    count = case["endpoint"]
    if "task_id" not in case:
        return [library / case["directory"] / "原图" / (
            "Input.png" if i == 0 else f"LDS_{i:02d}_eta_{i * .02:.2f}.png"
        ) for i in range(count + 1)]

    query_root = library.parent
    index = json.loads((query_root / "00_索引与参照" / "任务查询索引.json").read_text(encoding="utf-8"))
    entry = next(item for item in index if
                 item.get("section") == "主实验" and item.get("dataset") == "SciIR"
                 and item.get("method_label") == "LDS_Target-Reference"
                 and item.get("model") == case["query_model"]
                 and item.get("sample_id") == case["task_id"])
    record = json.loads(((query_root / entry["path"]).parent / "任务与来源.json").read_text(encoding="utf-8"))
    records = [record["anchor"]] + sorted(record["candidates"], key=lambda item: item["index"])[:count]
    images = []
    for item in records:
        path = Path(item["image"])
        if not path.is_file():
            path = query_root.parent / str(path).split("/ICLR实验/", 1)[1]
        images.append(path)
    return images


def build_case(case, library, output, work, ffmpeg):
    folder = output / case["id"]
    folder.mkdir(parents=True, exist_ok=True)
    frames = work / case["id"]
    frames.mkdir()
    count = case["endpoint"]
    prefix = case.get("asset_prefix", "")
    anchors = []
    for i, source in enumerate(source_images(case, library)):
        with Image.open(source) as original:
            image = original.convert("RGB").resize((640, 640), Image.Resampling.LANCZOS)
            image.save(frames / f"frame_{i:03d}.png")
            image.save(folder / f"{prefix}frame_{i:03d}.webp", lossless=True, method=6)
        anchors.append(dict(eta=round(i * .02, 2), time=round(.6 + 6 * i / count, 6),
                            src=f"showcase/{case['id']}/{prefix}frame_{i:03d}.webp"))
    for i in (count + 1, count + 2):
        shutil.copyfile(frames / f"frame_{count:03d}.png", frames / f"frame_{i:03d}.png")
    filters = (
        "minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:"
        "me=epzs:mb_size=16:search_param=32:vsbmc=1:scd=none,"
        "trim=start_frame=0:end_frame=181,setpts=PTS-STARTPTS,"
        "tpad=start=18:stop=35:start_mode=clone:stop_mode=clone,format=yuv420p"
    )
    raw_video = frames / "optical_transition.mp4"
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
               "-framerate", f"{count}/6", "-i", str(frames / "frame_%03d.png"),
               "-vf", filters, "-an", "-c:v", "libx264", "-crf", "17",
               "-preset", "fast", "-threads", "2", "-filter_threads", "1",
               "-g", "30", "-movflags", "+faststart", str(raw_video)]
    subprocess.run(command, check=True)
    video_name = f"{prefix}transition_smooth.mp4"
    timing = retime_video(raw_video, folder / video_name,
                          [anchor["time"] for anchor in anchors], ffmpeg)
    for anchor, time in zip(anchors, timing["anchor_times"]):
        anchor["time"] = round(time, 6)
    print(f"Built {case['id']}: {len(anchors)} real keyframes, endpoint eta={anchors[-1]['eta']:.2f}", flush=True)
    return {key: case[key] for key in ("id", "category", "title", "goal")} | dict(
        poster=anchors[0]["src"], video=f"showcase/{case['id']}/{video_name}", anchors=anchors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="rgdr-interpolation-") as directory:
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda case: build_case(case, args.library, args.output,
                                Path(directory), args.ffmpeg), CASES))
    metadata = dict(duration=12.4, transitionStart=.1, transitionDuration=12,
                    timing="visual-change-balanced", playbackRate=2, cases=results)
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    size = sum(p.stat().st_size for p in args.output.rglob("*") if p.is_file())
    print(f"Total published media: {size / 1024**2:.2f} MiB", flush=True)


if __name__ == "__main__":
    main()
