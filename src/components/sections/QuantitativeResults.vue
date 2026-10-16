<script setup>
import results from '../../data/quantitative.json'
import { assetUrl } from '../../utils/assets.js'
</script>

<template>
  <div class="quantitative-results" aria-label="Quantitative results averaged across four models">
    <div class="metric-grid">
      <article v-for="metric in results.metrics" :key="metric.id" class="metric-card" :aria-labelledby="`metric-${metric.id}`">
        <p class="metric-value">{{ metric.value }}<span class="metric-unit">{{ metric.unit }}</span></p>
        <h3 :id="`metric-${metric.id}`" class="metric-label">{{ metric.label }}</h3>
        <p class="metric-description">{{ metric.description }}</p>
      </article>
    </div>
    <p class="metric-scope">Equal-weight averages of the four models reported in <a :href="assetUrl('paper.pdf')" target="_blank" rel="noopener">Table 1</a>. Additional-image budgets are matched within each model.</p>
  </div>
</template>

<style scoped>
.quantitative-results { margin: 0 0 52px; }
.metric-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }
.metric-card { padding: 25px 30px 27px; min-width: 0; border: 1px solid #dce5ed; border-radius: 12px; background: #f8fafc; }
.metric-value { margin: 0 0 10px; color: var(--accent); font-size: 52px; font-weight: 700; line-height: 1.12; letter-spacing: -1.6px; font-variant-numeric: tabular-nums; }
.metric-unit { margin-left: 5px; font-size: 24px; font-weight: 500; letter-spacing: -.4px; }
.metric-label { margin: 0 0 9px; color: #354759; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: 700; line-height: 1.4; letter-spacing: .15px; }
.metric-description { margin: 0; color: #5c6874; font-size: 15px; line-height: 1.65; }
.metric-scope { max-width: 880px; margin: 17px auto 0; color: #6b7682; text-align: center; font-size: 12px; line-height: 1.7; }
.metric-scope a { text-decoration: underline; text-underline-offset: 2px; }
@media (max-width: 700px) {
  .quantitative-results { margin-bottom: 38px; }
  .metric-grid { gap: 14px; }
  .metric-card { padding: 22px; }
  .metric-value { font-size: 44px; }
  .metric-description { font-size: 14px; }
  .metric-scope { text-align: left; }
}
@media (max-width: 540px) {
  .metric-grid { grid-template-columns: minmax(0, 1fr); gap: 12px; }
  .metric-card { padding: 21px 23px; }
  .metric-value { font-size: 42px; }
}
</style>
