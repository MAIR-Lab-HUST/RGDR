<script setup>
import project from '../../data/project.json'
import PaperFigure from '../PaperFigure.vue'
</script>

<template>
  <section id="method" class="section-block page-width" aria-labelledby="method-title">
    <div class="section-intro reading-width">
      <p class="section-label">Method</p>
      <h2 id="method-title">{{ project.method.heading }}</h2>
    </div>
    <PaperFigure :figure="project.method_figure" />
  </section>
</template>

<style scoped>
:deep(.paper-figure figcaption) {
  max-width: 880px;
  margin: 28px auto 0;
  font-size: 16px;
  line-height: 1.9;
  color: inherit;
  text-align: justify;
}
@media (max-width: 700px) {
  :deep(.paper-figure figcaption) {
    margin-top: 24px;
    font-size: 15px;
    line-height: 1.8;
    text-align: left;
  }
}
</style>
