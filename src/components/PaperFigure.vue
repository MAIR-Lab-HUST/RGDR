<script setup>
import { assetUrl } from '../utils/assets.js'

defineProps({
  figure: { type: Object, required: true },
  eager: { type: Boolean, default: false },
})
</script>

<template>
  <figure class="paper-figure">
    <a class="figure-link" :href="assetUrl(figure.src)" target="_blank" rel="noopener"
       :aria-label="`Open full-size figure: ${figure.title}`">
      <img :src="assetUrl(figure.src)" :alt="figure.alt" :width="figure.width" :height="figure.height"
           :loading="eager ? 'eager' : 'lazy'" decoding="async" />
    </a>
    <figcaption>{{ figure.caption }}</figcaption>
  </figure>
</template>
