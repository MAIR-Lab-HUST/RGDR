<script setup>
import { Document, Files, Collection } from '@element-plus/icons-vue'
import project from '../../data/project.json'
import { assetUrl } from '../../utils/assets.js'
import hustLogo from '../../assets/logos/华中科技大学.svg'
import sorbonneLogo from '../../assets/logos/索邦大学.svg'
import zzuLogo from '../../assets/logos/郑州大学.png'

const icons = { paper: Document, code: Files, dataset: Collection }
const institutions = [
  { id: 'hust', name: 'Huazhong University of Science and Technology', logo: hustLogo, width: 202, height: 153 },
  { id: 'sorbonne', name: 'Sorbonne University', logo: sorbonneLogo, width: 389, height: 157 },
  { id: 'zzu', name: 'Zhengzhou University', logo: zzuLogo, width: 252, height: 252 },
]
const titleParts = project.title.split(' for ')
</script>

<template>
  <section id="top" class="hero page-width" aria-labelledby="paper-title">
    <div class="institution-logos" role="group" aria-label="Participating institutions">
      <div v-for="institution in institutions" :key="institution.id" class="institution-logo-slot">
        <img :class="['institution-logo', `institution-logo-${institution.id}`]"
             :src="institution.logo" :alt="institution.name"
             :width="institution.width" :height="institution.height" />
      </div>
    </div>
    <h1 id="paper-title">
      <span><strong class="title-acronym">{{ project.short_name }}:</strong> {{ titleParts[0] }}</span>
      <span v-if="titleParts.length > 1">{{ ' for ' + titleParts.slice(1).join(' for ') }}</span>
    </h1>
    <div class="authors" aria-label="Authors">
      <span v-for="author in project.authors" :key="author.name" class="author-name">
        {{ author.name }}<sup>{{ author.affiliations.join(',') }}<span v-if="author.marker" class="author-marker">{{ author.marker }}</span></sup>
      </span>
    </div>
    <div class="affiliations">
      <span v-for="affiliation in project.affiliations" :key="affiliation.id">
        <sup>{{ affiliation.id }}</sup>{{ affiliation.name }}
      </span>
    </div>
    <div class="author-notes">
      <span class="author-note"><span class="note-marker">*</span>Project leader and first author.</span>
      <span class="author-note"><span class="note-marker">†</span>Corresponding author.</span>
    </div>
    <div class="resource-buttons">
      <a v-for="link in project.links" :key="link.id" class="resource-button"
         :href="link.local ? assetUrl(link.href) : link.href" target="_blank" rel="noopener">
        <component :is="icons[link.id]" aria-hidden="true" />{{ link.label }}
      </a>
    </div>
  </section>
</template>
