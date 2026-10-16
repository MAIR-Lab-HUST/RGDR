<script setup>
import { assetUrl } from '../utils/assets.js'
</script>

<template>
  <footer class="site-footer">
    <div class="page-width footer-inner">
      <p>RGDR &nbsp; Reflection-Guided Dynamics Rectification</p>
      <div class="footer-actions">
        <a class="back-top" href="#top">Back to top ↑</a>
        <a class="back-top footer-credits" :href="assetUrl('credits.html')">Credits</a>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer-actions { display: flex; align-items: center; gap: 22px; }
.footer-credits { color: #7b8590; }
</style>
