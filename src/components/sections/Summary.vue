<script setup>
import project from '../../data/project.json'
</script>

<template>
  <section id="summary" class="summary-section section-block" aria-labelledby="summary-title">
    <div class="reading-width">
      <h2 id="summary-title" class="section-label">Summary</h2>
      <p class="summary-copy">{{ project.summary }}</p>
    </div>
  </section>
</template>
