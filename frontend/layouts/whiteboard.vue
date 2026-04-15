<template>
  <!-- Fullscreen layout for Excalidraw — no header/footer -->
  <div class="whiteboard-shell">
    <slot />
  </div>
</template>

<style scoped>
/*
  position: fixed + inset: 0 already gives us a fullscreen container without
  touching html/body — so we don't bleed overflow:hidden into other pages.
*/
.whiteboard-shell {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  overflow: hidden;
}
</style>
