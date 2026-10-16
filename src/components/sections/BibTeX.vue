<script setup>
import { ref } from 'vue'
import { CopyDocument, Check } from '@element-plus/icons-vue'
import project from '../../data/project.json'

const copied = ref(false)
const message = ref('')
let resetTimer

async function copyCitation() {
  try {
    await navigator.clipboard.writeText(project.bibtex)
    copied.value = true
    message.value = 'Citation copied.'
    clearTimeout(resetTimer)
    resetTimer = setTimeout(() => { copied.value = false; message.value = '' }, 2500)
  } catch {
    message.value = 'Please select and copy the citation below.'
  }
}
</script>

<template>
  <section id="citation" class="citation-section section-block reading-width" aria-labelledby="citation-title">
    <div class="citation-heading">
      <p class="section-label">Citation</p>
      <h2 id="citation-title"><span class="citation-acronym">RGDR:</span> Reflection-Guided Dynamics Rectification</h2>
      <p class="citation-description">Please cite this paper if you find RGDR useful for reflection-guided trajectory rectification, or if you use our code or dataset in your research.</p>
    </div>
    <div class="citation-card">
      <div class="citation-toolbar">
        <span class="citation-format">BibTeX</span>
        <button type="button" class="copy-button" @click="copyCitation">
          <component :is="copied ? Check : CopyDocument" aria-hidden="true" />{{ copied ? 'Copied' : 'Copy citation' }}
        </button>
      </div>
      <pre class="citation-code"><code>{{ project.bibtex }}</code></pre>
    </div>
    <p class="copy-status" aria-live="polite">{{ message }}</p>
  </section>
</template>

<style scoped>
.citation-section {
  width: min(880px, calc(100% - 48px));
  padding-top: 64px;
  padding-bottom: 60px;
}

.citation-heading {
  display: block;
  margin-bottom: 30px;
  text-align: center;
}

.section-label {
  margin-bottom: 24px;
}

.citation-heading h2 {
  max-width: 840px;
  margin: 0 auto 20px;
  font-size: 40px;
  font-weight: 700;
  line-height: 1.22;
  letter-spacing: -1px;
  text-wrap: balance;
}

.citation-acronym {
  color: var(--accent);
}

.citation-description {
  max-width: 760px;
  margin: 0 auto;
  color: #58636e;
  font-size: 16px;
  line-height: 1.8;
}

.citation-card {
  overflow: hidden;
  border: 1px solid #e1e7ed;
  border-radius: 12px;
  background: #f5f7f9;
}

.citation-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 20px;
  border-bottom: 1px solid #e1e7ed;
}

.citation-format {
  color: #687480;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: .3px;
}

.copy-button {
  min-height: 36px;
  padding: 6px 12px;
  border-color: #d9e1e8;
  background: #fff;
  font-size: 13px;
}

.copy-button:hover {
  border-color: #a9bdce;
  color: var(--accent);
}

.citation-code {
  margin: 0;
  padding: 22px 24px 24px;
  border-radius: 0;
  background: transparent;
  font-size: 13px;
  line-height: 1.8;
}

.copy-status {
  margin-top: 8px;
  text-align: right;
}

@media (max-width: 700px) {
  .citation-section {
    width: calc(100% - 32px);
    padding-top: 44px;
    padding-bottom: 38px;
  }

  .citation-heading {
    margin-bottom: 24px;
  }

  .citation-heading h2 {
    margin-bottom: 16px;
    font-size: 29px;
    line-height: 1.25;
    letter-spacing: -.5px;
  }

  .citation-description {
    font-size: 16px;
    line-height: 1.8;
  }

  .citation-toolbar {
    padding: 12px 14px;
  }

  .citation-code {
    padding: 18px 16px 20px;
    font-size: 12px;
  }
}
</style>
