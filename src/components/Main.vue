<script setup>
import Title from './sections/Title.vue'
import Summary from './sections/Summary.vue'
import Showcase from './sections/Showcase.vue'
import Method from './sections/Method.vue'
import QualitativeResults from './sections/QualitativeResults.vue'
import BibTeX from './sections/BibTeX.vue'
</script>

<template>
  <main id="main-content">
    <Title />
    <Showcase />
    <Summary />
    <Method />
    <QualitativeResults />
    <BibTeX />
  </main>
</template>
