<script setup>
import gallery from '../../data/gallery.json'
import QuantitativeResults from './QuantitativeResults.vue'
import { assetUrl } from '../../utils/assets.js'
</script>

<template>
  <section id="results" class="section-block page-width" aria-labelledby="results-title">
    <div class="section-intro reading-width">
      <h2 id="results-title" class="section-label">Results</h2>
      <p class="results-description">We apply RGDR to existing outputs from Stable Diffusion 3.5 Medium, SANA-1.5 1.6B, and FLUX.1-dev for text-to-image generation, and Qwen-Image-Edit-2511 for image editing. Results on PRISM-Bench and SciIR-Bench use matched additional-image budgets within each model.</p>
    </div>
    <QuantitativeResults />
    <p class="gallery-intro">The examples below compare each image before correction (Base) with its RGDR-rectified result.</p>
    <div class="gallery-categories">
      <section v-for="group in gallery.groups" :key="group.id" class="gallery-category" :aria-labelledby="`gallery-${group.id}-title`">
        <h3 :id="`gallery-${group.id}-title`">{{ group.label }}</h3>
        <div class="gallery-cases">
          <article v-for="item in group.cases" :key="item.id" class="gallery-case" :aria-label="item.title" :data-case-id="item.id" :data-selected-index="item.selectedIndex">
            <figure v-for="picture in item.images" :key="picture.src" class="gallery-picture">
              <figcaption :class="{ 'rgdr-label': picture.role === 'RGDR' }">{{ picture.role }}</figcaption>
              <a class="gallery-image" :href="assetUrl(picture.src)" target="_blank" rel="noopener" :aria-label="`Open ${picture.alt}`">
                <img :src="assetUrl(picture.src)" :alt="picture.alt" :width="picture.width" :height="picture.height" loading="lazy" decoding="async" />
              </a>
            </figure>
            <p v-if="item.caption" class="gallery-caption">{{ item.caption }}</p>
          </article>
        </div>
      </section>
    </div>
  </section>
</template>

<style scoped>
.results-description { max-width: 880px; margin: 0 auto; font-size: 16px; line-height: 1.8; text-align: center; }
.gallery-intro { max-width: 880px; margin: 0 auto 32px; color: #515b67; text-align: center; font-size: 16px; line-height: 1.8; }
.gallery-categories { display: grid; gap: 56px; }
.gallery-category { min-width: 0; }
.gallery-category > h3 { margin: 0 0 22px; padding-bottom: 12px; border-bottom: 1px solid var(--line); text-align: center; font-family: Arial, Helvetica, sans-serif; font-size: 22px; font-weight: 600; }
.gallery-cases { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 26px 30px; }
.gallery-case { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; min-width: 0; }
.gallery-picture { min-width: 0; margin: 0; }
.gallery-caption { grid-column: 1 / -1; margin: 5px 0 0; color: #56616d; text-align: center; font-size: 14px; line-height: 1.6; }
.gallery-picture figcaption { margin: 0 0 8px; color: #56616d; text-align: center; font-size: 14px; font-weight: 600; line-height: 1.4; }
.gallery-picture .rgdr-label { color: var(--accent); }
.gallery-image { display: block; min-width: 0; aspect-ratio: 1; overflow: hidden; border: 1px solid #e4e8ed; border-radius: 2px; background: #fff; }
.gallery-image img { display: block; width: 100%; height: 100%; object-fit: contain; }
.gallery-image:hover { border-color: #93aec3; }
@media (max-width: 700px) {
  .gallery-categories { gap: 40px; }
  .gallery-category > h3 { font-size: 20px; margin-bottom: 18px; }
  .gallery-cases { grid-template-columns: minmax(0, 1fr); gap: 22px; }
  .gallery-picture figcaption { font-size: 13px; margin-bottom: 6px; }
}
</style>
