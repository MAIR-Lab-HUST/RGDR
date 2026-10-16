<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import showcase from '../../data/showcase.json'
import { assetUrl } from '../../utils/assets.js'

const section = ref(null)
const videos = []
const viewports = []
const snapshots = showcase.cases.map(() => [])
const helpers = new Set()
const cancellation = new AbortController()
const currentTime = ref(0)
const playing = ref(false)
const prepared = ref(false)
const playbackError = ref('')
const duration = showcase.duration
const playbackRate = showcase.playbackRate || 1
const cases = showcase.cases
const frozenCount = 4
const metrics = ref(cases.map(() => ({ tile: 220, stride: 220, travel: 880 })))
const progress = computed(() => Math.min(1, currentTime.value / duration))
let frame = 0
let observer
let resizeObserver
let visible = false
let autoplayAttempted = false
let reducedMotion = false
let operation = 0

function measureTracks() {
  metrics.value = viewports.map(viewport => {
    const tile = Math.max(1, viewport.clientWidth / (frozenCount + 1))
    return { tile, stride: tile, travel: tile * frozenCount }
  })
}

function pause() {
  operation += 1
  videos.forEach(video => video?.pause())
  playing.value = false
  cancelAnimationFrame(frame)
}

function finish() {
  pause()
  currentTime.value = duration
}

function seek(time) {
  pause()
  const nextTime = Math.max(0, Math.min(duration - 0.015, Number(time)))
  currentTime.value = nextTime
  videos.forEach(video => {
    if (video?.readyState >= 1) video.currentTime = nextTime
  })
}

function tick() {
  if (!playing.value || !videos[0]) return
  const master = videos[0]
  currentTime.value = master.currentTime
  if (master.ended || master.currentTime >= duration - 0.04) {
    finish()
    return
  }
  videos.slice(1).forEach(video => {
    if (video?.readyState >= 2 && Math.abs(video.currentTime - master.currentTime) > 0.12) {
      video.currentTime = master.currentTime
    }
  })
  frame = requestAnimationFrame(tick)
}

async function play() {
  if (playing.value || !prepared.value) return
  if (currentTime.value >= duration - 0.05) seek(0)
  const requested = ++operation
  playbackError.value = ''
  try {
    await Promise.all(videos.map(video => {
      video.playbackRate = playbackRate
      if (video.readyState >= 1) video.currentTime = currentTime.value
      return video.play()
    }))
    if (requested !== operation) return
    playing.value = true
    frame = requestAnimationFrame(tick)
  } catch {
    if (requested !== operation) return
    pause()
    playbackError.value = 'Press play to view the transition.'
  }
}

function replay() {
  seek(0)
  play()
}

function tryAutoplay() {
  if (visible && !document.hidden && prepared.value && !reducedMotion && !autoplayAttempted &&
      videos.length === cases.length && videos.every(video => video?.readyState >= 2)) {
    autoplayAttempted = true
    replay()
  }
}

function loaded(index) {
  const video = videos[index]
  if (video) video.playbackRate = playbackRate
  if (video && currentTime.value > 0) video.currentTime = Math.min(currentTime.value, duration - 0.015)
  tryAutoplay()
}

function exactAnchor(item) {
  if (playing.value) return undefined
  const anchors = item.anchors
  if (currentTime.value <= anchors[0].time) return anchors[0]
  if (currentTime.value >= anchors[anchors.length - 1].time) return anchors[anchors.length - 1]
  return anchors.find(anchor => Math.abs(anchor.time - currentTime.value) < 0.035)
}

function waitForMedia(video, eventName, action) {
  return new Promise((resolve, reject) => {
    const cleanup = () => {
      video.removeEventListener(eventName, done)
      video.removeEventListener('error', failed)
      cancellation.signal.removeEventListener('abort', cancelled)
    }
    const done = () => { cleanup(); resolve() }
    const failed = () => { cleanup(); reject(new Error('Video could not be loaded.')) }
    const cancelled = () => { cleanup(); reject(new Error('Cancelled.')) }
    video.addEventListener(eventName, done, { once: true })
    video.addEventListener('error', failed, { once: true })
    cancellation.signal.addEventListener('abort', cancelled, { once: true })
    action()
  })
}

async function prepareSnapshots(index) {
  const helper = document.createElement('video')
  helper.muted = true
  helper.playsInline = true
  helper.preload = 'auto'
  helpers.add(helper)
  try {
    await waitForMedia(helper, 'loadeddata', () => {
      helper.src = assetUrl(cases[index].video)
      helper.load()
    })
    for (let slot = 0; slot < frozenCount; slot += 1) {
      if (cancellation.signal.aborted) return
      const time = duration * slot / frozenCount
      if (Math.abs(helper.currentTime - time) > 0.001) {
        await waitForMedia(helper, 'seeked', () => { helper.currentTime = time })
      }
      const canvas = snapshots[index][slot]
      canvas.getContext('2d').drawImage(helper, 0, 0, canvas.width, canvas.height)
    }
  } finally {
    helper.pause()
    helper.removeAttribute('src')
    helper.load()
    helpers.delete(helper)
  }
}

async function prepareSequences() {
  let next = 0
  const worker = async () => {
    while (next < cases.length && !cancellation.signal.aborted) {
      const index = next++
      try { await prepareSnapshots(index) } catch {
        if (cancellation.signal.aborted) return
      }
    }
  }
  await Promise.all([worker(), worker()])
  if (cancellation.signal.aborted) return
  prepared.value = true
  tryAutoplay()
}

function visibilityChanged() {
  if (document.hidden) {
    pause()
    autoplayAttempted = false
  } else {
    tryAutoplay()
  }
}

onMounted(() => {
  reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  measureTracks()
  resizeObserver = new ResizeObserver(measureTracks)
  viewports.forEach(viewport => resizeObserver.observe(viewport))
  observer = new IntersectionObserver(entries => {
    visible = entries[0].isIntersecting
    if (visible) {
      tryAutoplay()
    } else {
      pause()
      autoplayAttempted = false
    }
  }, { threshold: 0 })
  observer.observe(section.value)
  document.addEventListener('visibilitychange', visibilityChanged)
  prepareSequences()
})

onBeforeUnmount(() => {
  cancellation.abort()
  pause()
  observer?.disconnect()
  resizeObserver?.disconnect()
  helpers.forEach(helper => { helper.pause(); helper.removeAttribute('src'); helper.load() })
  document.removeEventListener('visibilitychange', visibilityChanged)
})
</script>

<template>
  <section id="showcase" ref="section" class="showcase-section" aria-labelledby="showcase-title">
    <div class="page-width showcase-content">
      <h2 id="showcase-title" class="section-label">Examples</h2>
      <div class="showcase-controls">
        <button type="button" class="play-button" :disabled="!prepared" :aria-label="playing ? 'Pause all examples' : 'Play all examples'" @click="playing ? pause() : play()">
          <svg v-if="playing" viewBox="0 0 20 20" aria-hidden="true"><path d="M6 4v12M14 4v12" /></svg>
          <svg v-else viewBox="0 0 20 20" aria-hidden="true"><path d="m6 3 11 7-11 7Z" /></svg>
          <span>{{ !prepared ? 'Loading' : playing ? 'Pause' : 'Play' }}</span>
        </button>
        <label class="timeline">
          <span>Increasing correction strength η →</span>
          <input type="range" min="0" :max="duration" step="0.01" :value="currentTime"
            aria-label="Correction strength eta"
            :aria-valuetext="`${Math.round(progress * 100)} percent through increasing correction strength`"
            @input="seek($event.target.value)" />
        </label>
        <button type="button" class="replay-button" :disabled="!prepared" @click="replay()">
          <svg viewBox="0 0 20 20" aria-hidden="true"><path d="M4 7a7 7 0 1 1-1 6M4 2v5h5" /></svg>
          <span>Replay</span>
        </button>
      </div>
      <p v-if="playbackError" class="playback-message" role="status">{{ playbackError }}</p>
      <div class="showcase-grid">
        <article v-for="(item, index) in cases" :key="item.id" class="example">
          <header class="example-heading">
            <span class="example-category">{{ item.category }}</span>
            <h2>{{ item.title }}</h2>
          </header>
          <div :ref="element => { viewports[index] = element }" class="sequence-viewport" :style="{ '--frame-size': `${metrics[index].tile}px` }" :aria-label="`${item.category}: correction sequence`">
            <div class="sequence-track" :style="{ width: `${metrics[index].travel + metrics[index].tile}px` }">
              <canvas v-for="slot in frozenCount" :key="slot"
                :ref="element => { snapshots[index][slot - 1] = element }"
                v-show="progress >= (slot - 1) / frozenCount"
                width="480" height="480" class="frozen-picture"
                :style="{ left: `${(slot - 1) * metrics[index].stride}px` }"
                aria-hidden="true"></canvas>
              <div class="moving-picture"
                   :style="{ transform: `translate3d(${metrics[index].travel * progress}px, 0, 0)` }">
                <video :ref="element => { videos[index] = element }"
                  :src="assetUrl(item.video)" :poster="assetUrl(item.poster)"
                  :aria-label="`${item.title}: correction progression`"
                  muted playsinline preload="auto" disablepictureinpicture
                  @loadeddata="loaded(index)" @ended="index === 0 && finish()"></video>
                <img v-if="exactAnchor(item)" :src="assetUrl(exactAnchor(item).src)" alt="" class="actual-keyframe" />
              </div>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.showcase-section { padding: 0 0 64px; }
.showcase-content { border-top: 1px dashed #c8d1da; padding-top: 16px; }
.showcase-grid { display: grid; grid-template-columns: minmax(0, 1fr); gap: 34px; }
.example { min-width: 0; }
.example-heading { display: flex; align-items: baseline; gap: 18px; margin: 0 0 12px; }
.example-category { flex: 0 0 105px; font-size: 12px; letter-spacing: 1.3px; text-transform: uppercase; font-weight: 700; color: var(--accent); }
.example-heading h2 { font-family: Arial, Helvetica, sans-serif; font-size: 18px; font-weight: 500; line-height: 1.5; letter-spacing: -.2px; margin: 0; }
.sequence-viewport { --frame-size: 220px; position: relative; height: calc(var(--frame-size) + 2px); overflow: hidden; scroll-behavior: auto; border: 1px solid #e0e5ea; border-radius: 3px; background: #fff; }
.sequence-track { position: relative; height: var(--frame-size); }
.moving-picture, .frozen-picture { position: absolute; top: 0; width: var(--frame-size); height: var(--frame-size); background: #fff; }
.moving-picture { z-index: 1; left: 0; will-change: transform; }
.moving-picture video, .actual-keyframe { position: absolute; width: 100%; height: 100%; inset: 0; object-fit: contain; }
.actual-keyframe { pointer-events: none; }
.showcase-controls { position: sticky; top: 62px; z-index: 10; display: flex; align-items: center; gap: 24px; margin: 0 auto 24px; padding: 12px 0; width: min(800px, 100%); background: #fff; }
.play-button, .replay-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 42px; border: 0; padding: 6px 0; background: transparent; color: #45515e; font-size: 13px; }
.play-button { min-width: 70px; }
.play-button:disabled, .replay-button:disabled { cursor: wait; opacity: .55; }
.play-button svg, .replay-button svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.play-button svg path[d^="m6"] { fill: currentColor; stroke: none; }
.play-button:hover, .replay-button:hover { color: var(--accent); }
.timeline { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 6px; text-align: center; color: #68717c; font-size: 12px; line-height: 1.4; }
.timeline input { display: block; width: 100%; margin: 0; height: 20px; cursor: pointer; accent-color: var(--accent); }
.playback-message { text-align: center; font-size: 12px; color: var(--muted); margin: 8px 0 18px; }
@media (max-width: 700px) {
  .showcase-controls { top: 56px; }
}
@media (max-width: 600px) {
  .showcase-section { padding-bottom: 42px; }
  .showcase-content { padding-top: 10px; }
  .showcase-grid { gap: 28px; }
  .example-heading { display: block; }
  .example-category { display: block; margin-bottom: 5px; font-size: 11px; }
  .example-heading h2 { font-size: 16px; }
  .showcase-controls { gap: 15px; margin-bottom: 20px; }
  .play-button, .replay-button { gap: 5px; font-size: 12px; }
  .play-button { min-width: 60px; }
}
</style>
