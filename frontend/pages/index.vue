<script setup>
// Redirect to login page
navigateTo('/login')
</script>

<template>
  <div class="min-h-screen bg-[var(--background)] flex items-center justify-center">
    <div class="text-center">
      <div class="w-8 h-8 border-2 border-[var(--foreground)] border-t-transparent animate-spin mx-auto mb-4"></div>
      <p class="text-sm text-[var(--muted-foreground)] uppercase tracking-widest font-mono">
        Redirecting...
      </p>
    </div>
  </div>
</template>
