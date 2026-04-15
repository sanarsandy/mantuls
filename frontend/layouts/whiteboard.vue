<template>
  <!-- Fullscreen layout for Excalidraw — no header/footer -->
  <div class="whiteboard-shell">
    <slot />
  </div>
</template>

<style>
/* Reset everything so Excalidraw gets the full viewport */
html, body {
  margin: 0;
  padding: 0;
  overflow: hidden;
  height: 100%;
  width: 100%;
}

.whiteboard-shell {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
}
</style>
