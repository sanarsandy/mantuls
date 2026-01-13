<template>
  <div>
    <!-- Back Link -->
    <NuxtLink 
      to="/dashboard" 
      class="inline-flex items-center text-sm uppercase tracking-widest text-[var(--muted-foreground)] hover:text-[var(--foreground)] mb-8 transition-colors duration-100"
    >
      <Icon name="heroicons:arrow-left" class="w-4 h-4 mr-2" />
      Back to Tools
    </NuxtLink>

    <!-- Page Header -->
    <div class="flex flex-col md:flex-row md:justify-between md:items-end mb-8 pb-8 border-b-4 border-[var(--foreground)]">
      <div>
        <h1 class="font-serif text-4xl md:text-5xl font-bold tracking-tighter">
          OCR SCANNER
        </h1>
        <p class="text-[var(--muted-foreground)] mt-2 text-lg">
          Extract text from images and PDF documents
        </p>
      </div>
      <NuxtLink 
        to="/tools/ocr/scan" 
        class="btn-mono-primary mt-4 md:mt-0 no-underline"
      >
        <Icon name="heroicons:plus" class="w-4 h-4 mr-2" />
        New Scan
      </NuxtLink>
    </div>

    <!-- Empty State -->
    <div class="border-2 border-[var(--foreground)] p-12 md:p-16 text-center section-textured">
      <!-- Icon -->
      <div class="inline-flex items-center justify-center w-20 h-20 border-2 border-[var(--foreground)] mb-6">
        <Icon name="heroicons:document-magnifying-glass" class="w-10 h-10 text-[var(--muted-foreground)]" />
      </div>
      
      <!-- Text -->
      <h3 class="font-serif text-2xl font-bold tracking-tight mb-2">
        No scans yet
      </h3>
      <p class="text-[var(--muted-foreground)] mb-8 max-w-sm mx-auto">
        Upload an image or PDF to extract text using OCR technology
      </p>
      
      <!-- Decorative rule -->
      <div class="flex items-center justify-center mb-8">
        <div class="w-16 h-0.5 bg-[var(--border-light)]"></div>
        <div class="w-2 h-2 border border-[var(--border-light)] mx-2"></div>
        <div class="w-16 h-0.5 bg-[var(--border-light)]"></div>
      </div>
      
      <!-- CTA Link -->
      <NuxtLink 
        to="/tools/ocr/scan" 
        class="inline-flex items-center text-sm uppercase tracking-widest text-[var(--foreground)] hover:text-[var(--muted-foreground)] transition-colors duration-100"
      >
        <Icon name="heroicons:arrow-up-tray" class="w-4 h-4 mr-2" />
        Start Scanning
      </NuxtLink>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  middleware: ['auth']
})

useHead({
  title: 'OCR Scanner — LMAN Office Tools'
})
</script>
