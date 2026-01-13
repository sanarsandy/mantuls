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
        IMAGE CONVERTER
      </h1>
      <p class="text-[var(--muted-foreground)] mt-2 text-lg">
        Convert images between JPG, PNG, and WEBP formats
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
              name="heroicons:photo" 
              class="w-8 h-8"
              :class="isDragging ? 'text-[var(--background)]' : 'text-[var(--muted-foreground)]'"
            />
          </div>
          
          <p class="font-serif text-lg font-medium mb-1">
            Drop image file here or click to browse
          </p>
          <p class="text-sm" :class="isDragging ? 'text-[var(--background)]/70' : 'text-[var(--muted-foreground)]'">
            Supported: JPG, PNG, WEBP
          </p>
        </div>

        <!-- File Selected -->
        <div v-else class="space-y-6">
          <!-- Preview -->
          <div class="border-2 border-[var(--foreground)] p-4">
            <div class="aspect-video bg-[var(--muted)] flex items-center justify-center overflow-hidden">
              <img 
                v-if="previewUrl" 
                :src="previewUrl" 
                class="max-h-full max-w-full object-contain"
                alt="Preview"
              />
            </div>
            <div class="flex items-center justify-between mt-4 pt-4 border-t border-[var(--border-light)]">
              <div>
                <p class="font-medium">{{ file.name }}</p>
                <p class="text-xs text-[var(--muted-foreground)]">
                  {{ formatSize(file.size) }} • {{ getExtension(file.name).toUpperCase() }}
                </p>
              </div>
              <button 
                @click="clearFile" 
                class="text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                <Icon name="heroicons:x-mark" class="w-5 h-5" />
              </button>
            </div>
          </div>

          <!-- Format Selection -->
          <div class="border border-[var(--border-light)] p-6">
            <label class="label-mono mb-3">Convert to</label>
            <div class="grid grid-cols-3 gap-3">
              <button 
                v-for="format in formats" 
                :key="format"
                @click="targetFormat = format"
                class="p-4 border-2 transition-colors text-center"
                :class="targetFormat === format 
                  ? 'border-[var(--foreground)] bg-[var(--foreground)] text-[var(--background)]' 
                  : 'border-[var(--border-light)] hover:border-[var(--foreground)]'"
              >
                <span class="font-mono font-bold">{{ format.toUpperCase() }}</span>
              </button>
            </div>
          </div>

          <!-- Quality (for JPG/WEBP) -->
          <div v-if="targetFormat !== 'png'" class="border border-[var(--border-light)] p-6">
            <label class="label-mono mb-3">Quality: {{ quality }}%</label>
            <input 
              type="range" 
              v-model="quality" 
              min="10" 
              max="100" 
              class="w-full h-2 bg-[var(--muted)] appearance-none cursor-pointer"
            />
            <div class="flex justify-between text-xs text-[var(--muted-foreground)] mt-2">
              <span>Smaller file</span>
              <span>Better quality</span>
            </div>
          </div>
        </div>

        <input 
          ref="fileInput" 
          type="file" 
          class="hidden" 
          accept=".jpg,.jpeg,.png,.webp"
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
          <p class="font-serif font-bold text-lg mb-4">Image Converted Successfully!</p>
          <a 
            :href="downloadUrl" 
            :download="`converted.${targetFormat}`"
            class="btn-mono-primary inline-flex"
          >
            <Icon name="heroicons:arrow-down-tray" class="w-4 h-4 mr-2" />
            Download {{ targetFormat.toUpperCase() }}
          </a>
        </div>
      </div>

      <!-- Action Button -->
      <div v-if="file && !downloadUrl" class="p-6 border-t-2 border-[var(--foreground)] bg-[var(--muted)]">
        <button 
          @click="convertImage" 
          :disabled="processing"
          class="btn-mono-primary w-full"
        >
          <span v-if="processing" class="flex items-center justify-center">
            <div class="w-4 h-4 border-2 border-[var(--background)]/30 border-t-[var(--background)] animate-spin mr-2"></div>
            Converting...
          </span>
          <span v-else class="flex items-center justify-center">
            <Icon name="heroicons:arrow-path" class="w-4 h-4 mr-2" />
            Convert to {{ targetFormat.toUpperCase() }}
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
  title: 'Image Converter — LMAN Office Tools'
})

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const formats = ['jpg', 'png', 'webp']

const isDragging = ref(false)
const file = ref(null)
const previewUrl = ref(null)
const targetFormat = ref('jpg')
const quality = ref(85)
const processing = ref(false)
const error = ref(null)
const downloadUrl = ref(null)

const handleFileSelect = (event) => {
  const selectedFile = event.target.files[0]
  if (selectedFile && selectedFile.type.startsWith('image/')) {
    setFile(selectedFile)
  }
}

const handleDrop = (event) => {
  isDragging.value = false
  const droppedFile = event.dataTransfer.files[0]
  if (droppedFile && droppedFile.type.startsWith('image/')) {
    setFile(droppedFile)
  }
}

const setFile = (f) => {
  file.value = f
  error.value = null
  downloadUrl.value = null
  
  // Create preview
  const reader = new FileReader()
  reader.onload = (e) => {
    previewUrl.value = e.target.result
  }
  reader.readAsDataURL(f)
  
  // Set default target format (different from source)
  const ext = getExtension(f.name)
  targetFormat.value = ext === 'jpg' || ext === 'jpeg' ? 'png' : 'jpg'
}

const clearFile = () => {
  file.value = null
  previewUrl.value = null
  downloadUrl.value = null
}

const getExtension = (filename) => {
  return filename.split('.').pop().toLowerCase()
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const convertImage = async () => {
  if (!file.value) return
  
  processing.value = true
  error.value = null
  downloadUrl.value = null

  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('format', targetFormat.value)
    formData.append('quality', quality.value)

    const response = await fetch(`${apiBase}/api/v1/tools/image-converter`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Failed to convert image')
    }

    const blob = await response.blob()
    downloadUrl.value = URL.createObjectURL(blob)
  } catch (err) {
    error.value = err.message
  } finally {
    processing.value = false
  }
}
</script>
