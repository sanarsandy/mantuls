<template>
  <div class="max-w-3xl mx-auto">
    <!-- Back Link -->
    <NuxtLink 
      to="/dashboard" 
      class="inline-flex items-center text-sm uppercase tracking-widest text-[var(--muted-foreground)] hover:text-[var(--foreground)] mb-8 transition-colors duration-100"
    >
      <Icon name="heroicons:arrow-left" class="w-4 h-4 mr-2" />
      Back to Tools
    </NuxtLink>

    <!-- Page Header -->
    <div class="mb-8 pb-8 border-b-4 border-[var(--foreground)]">
      <h1 class="font-serif text-4xl md:text-5xl font-bold tracking-tighter">
        COMPRESS PDF
      </h1>
      <p class="text-[var(--muted-foreground)] mt-2 text-lg">
        Reduce PDF file size while maintaining quality
      </p>
    </div>

    <!-- Upload Area -->
    <div class="border-2 border-[var(--foreground)] bg-[var(--background)]">
      <div class="p-8">
        <!-- Drop Zone (when no file) -->
        <div 
          v-if="!file"
          class="border-2 border-dashed border-[var(--foreground)] p-12 text-center cursor-pointer transition-colors duration-100"
          :class="{ 
            'bg-[var(--foreground)] text-[var(--background)]': isDragging,
            'hover:bg-[var(--muted)]': !isDragging
          }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
          @click="$refs.fileInput.click()"
        >
          <div 
            class="inline-flex items-center justify-center w-16 h-16 border-2 mb-6 transition-colors duration-100"
            :class="isDragging ? 'border-[var(--background)]' : 'border-[var(--foreground)]'"
          >
            <Icon 
              name="heroicons:archive-box-arrow-down" 
              class="w-8 h-8"
              :class="isDragging ? 'text-[var(--background)]' : 'text-[var(--muted-foreground)]'"
            />
          </div>
          
          <p class="font-serif text-lg font-medium mb-1">
            Drop PDF file here or click to browse
          </p>
          <p class="text-sm" :class="isDragging ? 'text-[var(--background)]/70' : 'text-[var(--muted-foreground)]'">
            Select a PDF file to compress
          </p>
        </div>

        <!-- File Selected -->
        <div v-else class="space-y-6">
          <div class="flex items-center justify-between p-4 border-2 border-[var(--foreground)]">
            <div class="flex items-center space-x-4">
              <div class="w-12 h-12 border-2 border-[var(--foreground)] flex items-center justify-center">
                <Icon name="heroicons:document" class="w-6 h-6" />
              </div>
              <div>
                <p class="font-medium">{{ file.name }}</p>
                <p class="text-xs text-[var(--muted-foreground)]">Original size: {{ formatSize(file.size) }}</p>
              </div>
            </div>
            <button 
              @click="file = null" 
              class="text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
            >
              <Icon name="heroicons:x-mark" class="w-5 h-5" />
            </button>
          </div>

          <!-- Compression Level -->
          <div class="border border-[var(--border-light)] p-6">
            <label class="label-mono mb-3">Compression Level</label>
            <div class="space-y-3">
              <label class="flex items-center cursor-pointer">
                <input 
                  type="radio" 
                  v-model="compressionLevel" 
                  value="low" 
                  class="w-4 h-4 border-2 border-[var(--foreground)] appearance-none checked:bg-[var(--foreground)]"
                />
                <span class="ml-3">
                  <span class="font-medium">Low</span>
                  <span class="text-sm text-[var(--muted-foreground)] ml-2">— Best quality, smaller reduction</span>
                </span>
              </label>
              <label class="flex items-center cursor-pointer">
                <input 
                  type="radio" 
                  v-model="compressionLevel" 
                  value="medium" 
                  class="w-4 h-4 border-2 border-[var(--foreground)] appearance-none checked:bg-[var(--foreground)]"
                />
                <span class="ml-3">
                  <span class="font-medium">Medium</span>
                  <span class="text-sm text-[var(--muted-foreground)] ml-2">— Balanced quality and size</span>
                </span>
              </label>
              <label class="flex items-center cursor-pointer">
                <input 
                  type="radio" 
                  v-model="compressionLevel" 
                  value="high" 
                  class="w-4 h-4 border-2 border-[var(--foreground)] appearance-none checked:bg-[var(--foreground)]"
                />
                <span class="ml-3">
                  <span class="font-medium">High</span>
                  <span class="text-sm text-[var(--muted-foreground)] ml-2">— Maximum compression, may affect quality</span>
                </span>
              </label>
            </div>
          </div>
        </div>

        <input 
          ref="fileInput" 
          type="file" 
          class="hidden" 
          accept=".pdf"
          @change="handleFileSelect"
        />

        <!-- Error Message -->
        <div v-if="error" class="alert-mono-error mt-6 flex items-start space-x-3">
          <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p class="text-sm">{{ error }}</p>
        </div>

        <!-- Success Message -->
        <div v-if="downloadUrl" class="alert-mono-success mt-6 text-center">
          <Icon name="heroicons:check-circle" class="w-12 h-12 mx-auto mb-4" />
          <p class="font-serif font-bold text-lg mb-2">PDF Compressed Successfully!</p>
          <p v-if="compressedSize" class="text-sm text-[var(--muted-foreground)] mb-4">
            {{ formatSize(file.size) }} → {{ formatSize(compressedSize) }} 
            <span class="font-mono">({{ Math.round((1 - compressedSize / file.size) * 100) }}% smaller)</span>
          </p>
          <a 
            :href="downloadUrl" 
            download="compressed.pdf"
            class="btn-mono-primary inline-flex"
          >
            <Icon name="heroicons:arrow-down-tray" class="w-4 h-4 mr-2" />
            Download Compressed PDF
          </a>
        </div>
      </div>

      <!-- Action Button -->
      <div v-if="file && !downloadUrl" class="p-6 border-t-2 border-[var(--foreground)] bg-[var(--muted)]">
        <button 
          @click="compressPDF" 
          :disabled="processing"
          class="btn-mono-primary w-full"
        >
          <span v-if="processing" class="flex items-center justify-center">
            <div class="w-4 h-4 border-2 border-[var(--background)]/30 border-t-[var(--background)] animate-spin mr-2"></div>
            Compressing...
          </span>
          <span v-else class="flex items-center justify-center">
            <Icon name="heroicons:archive-box-arrow-down" class="w-4 h-4 mr-2" />
            Compress PDF
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  middleware: ['auth']
})

useHead({
  title: 'Compress PDF — LMAN Office Tools'
})

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const isDragging = ref(false)
const file = ref(null)
const compressionLevel = ref('medium')
const processing = ref(false)
const error = ref(null)
const downloadUrl = ref(null)
const compressedSize = ref(null)

const handleFileSelect = (event) => {
  const selectedFile = event.target.files[0]
  if (selectedFile && selectedFile.type === 'application/pdf') {
    file.value = selectedFile
    error.value = null
    downloadUrl.value = null
    compressedSize.value = null
  }
}

const handleDrop = (event) => {
  isDragging.value = false
  const droppedFile = event.dataTransfer.files[0]
  if (droppedFile && droppedFile.type === 'application/pdf') {
    file.value = droppedFile
    error.value = null
    downloadUrl.value = null
    compressedSize.value = null
  }
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const compressPDF = async () => {
  if (!file.value) return
  
  processing.value = true
  error.value = null
  downloadUrl.value = null

  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('level', compressionLevel.value)

    const response = await fetch(`${apiBase}/api/v1/tools/compress-pdf`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Failed to compress PDF')
    }

    const blob = await response.blob()
    compressedSize.value = blob.size
    downloadUrl.value = URL.createObjectURL(blob)
  } catch (err) {
    error.value = err.message
  } finally {
    processing.value = false
  }
}
</script>
