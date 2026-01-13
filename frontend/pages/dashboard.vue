<template>
  <div>
    <!-- Page Header -->
    <div class="mb-12 pb-8 border-b-4 border-[var(--foreground)]">
      <div class="flex items-start justify-between">
        <div>
          <h1 class="font-serif text-4xl md:text-5xl font-bold tracking-tighter">
            TOOLS
          </h1>
          <p class="text-[var(--muted-foreground)] mt-2 text-lg">
            Digital tools for modern office productivity
          </p>
        </div>
        <NuxtLink 
          to="/guide" 
          class="flex items-center gap-2 px-4 py-2 border-2 border-[var(--foreground)] hover:bg-[var(--foreground)] hover:text-[var(--background)] transition-colors"
        >
          <Icon name="heroicons:book-open" class="w-5 h-5" />
          <span class="hidden sm:inline">Guides</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Tools Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      
      <!-- OCR Scanner -->
      <NuxtLink 
        to="/tools/ocr" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:document-magnifying-glass" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">OCR Scanner</h3>
        <p class="text-sm opacity-70">
          Extract text from images and PDF documents
        </p>
      </NuxtLink>

      <!-- Merge PDF -->
      <NuxtLink 
        to="/tools/merge-pdf" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:document-duplicate" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">Merge PDF</h3>
        <p class="text-sm opacity-70">
          Combine multiple PDF files into one
        </p>
      </NuxtLink>

      <!-- Split PDF -->
      <NuxtLink 
        to="/tools/split-pdf" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:scissors" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">Split PDF</h3>
        <p class="text-sm opacity-70">
          Split PDF into individual pages
        </p>
      </NuxtLink>

      <!-- Compress PDF -->
      <NuxtLink 
        to="/tools/compress-pdf" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:archive-box-arrow-down" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">Compress PDF</h3>
        <p class="text-sm opacity-70">
          Reduce PDF file size while maintaining quality
        </p>
      </NuxtLink>

      <!-- Image Converter -->
      <NuxtLink 
        to="/tools/image-converter" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:photo" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">Image Converter</h3>
        <p class="text-sm opacity-70">
          Convert images between JPG, PNG, and WEBP
        </p>
      </NuxtLink>

      <!-- QR Code Generator -->
      <NuxtLink 
        to="/tools/qr-generator" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:qr-code" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">QR Code Generator</h3>
        <p class="text-sm opacity-70">
          Generate QR codes for links, text, or data
        </p>
      </NuxtLink>

      <!-- Protect PDF -->
      <NuxtLink 
        to="/tools/protect-pdf" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:lock-closed" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">Protect PDF</h3>
        <p class="text-sm opacity-70">
          Encrypt PDF with password
        </p>
      </NuxtLink>

      <!-- Unlock PDF -->
      <NuxtLink 
        to="/tools/unlock-pdf" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:lock-open" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">Unlock PDF</h3>
        <p class="text-sm opacity-70">
          Remove password from PDF
        </p>
      </NuxtLink>

      <!-- Remove Background -->
      <NuxtLink 
        to="/tools/remove-bg" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:sparkles" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">Remove BG</h3>
        <p class="text-sm opacity-70">
          Remove image background with AI
        </p>
      </NuxtLink>

      <!-- PDF to Word -->
      <NuxtLink 
        to="/tools/pdf-to-word" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:document-arrow-down" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">PDF to Word</h3>
        <p class="text-sm opacity-70">
          Convert PDF to editable Word document
        </p>
      </NuxtLink>

      <!-- PDF to Excel -->
      <NuxtLink 
        to="/tools/pdf-to-excel" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:table-cells" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">PDF to Excel</h3>
        <p class="text-sm opacity-70">
          Convert PDF tables to editable Excel spreadsheet
        </p>
      </NuxtLink>

      <!-- Watermark PDF -->
      <NuxtLink 
        to="/tools/watermark-pdf" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:paint-brush" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">Watermark PDF</h3>
        <p class="text-sm opacity-70">
          Add text watermark to PDF documents
        </p>
      </NuxtLink>

      <!-- Word to PDF -->
      <NuxtLink 
        to="/tools/word-to-pdf" 
        class="group block border-2 border-[var(--foreground)] p-8 transition-all duration-100 hover:bg-[var(--foreground)] hover:text-[var(--background)] no-underline"
      >
        <div class="w-14 h-14 border-2 border-current flex items-center justify-center mb-6 transition-colors duration-100">
          <Icon name="heroicons:document-arrow-up" class="w-7 h-7" />
        </div>
        <h3 class="font-serif text-xl font-bold mb-2">Word to PDF</h3>
        <p class="text-sm opacity-70">
          Convert Word documents to PDF format
        </p>
      </NuxtLink>

    </div>
  </div>
</template>

<script setup>
definePageMeta({
  middleware: ['auth']
})

useHead({
  title: 'Dashboard — ManTuls'
})
</script>
