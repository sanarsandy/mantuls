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
        MERGE PDF
      </h1>
      <p class="text-[var(--muted-foreground)] mt-2 text-lg">
        Combine multiple PDF files into one document
      </p>
    </div>

    <!-- Upload Area -->
    <div class="border-2 border-[var(--foreground)] bg-[var(--background)]">
      <div class="p-8">
        <!-- Drop Zone -->
        <div 
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
              name="heroicons:document-plus" 
              class="w-8 h-8"
              :class="isDragging ? 'text-[var(--background)]' : 'text-[var(--muted-foreground)]'"
            />
          </div>
          
          <p class="font-serif text-lg font-medium mb-1">
            Drop PDF files here or click to browse
          </p>
          <p class="text-sm" :class="isDragging ? 'text-[var(--background)]/70' : 'text-[var(--muted-foreground)]'">
            Select multiple PDF files to merge
          </p>
        </div>

        <input 
          ref="fileInput" 
          type="file" 
          class="hidden" 
          accept=".pdf"
          multiple
          @change="handleFileSelect"
        />

        <!-- File List -->
        <client-only>
          <div v-if="files.length > 0" class="mt-8">
            <label class="label-mono mb-4">Files to merge ({{ files.length }}) - Drag to reorder</label>
            <draggable 
              v-model="files" 
              item-key="name"
              class="space-y-2"
              ghost-class="opacity-50"
            >
              <template #item="{ element: file, index }">
                <div 
                  class="flex items-center justify-between p-4 border border-[var(--border-light)] hover:border-[var(--foreground)] transition-colors cursor-move bg-[var(--background)]"
                >
                  <div class="flex items-center space-x-4">
                    <div class="w-8 h-8 border border-[var(--foreground)] flex items-center justify-center text-sm font-mono">
                      {{ index + 1 }}
                    </div>
                    <div>
                      <p class="font-medium">{{ file.name }}</p>
                      <p class="text-xs text-[var(--muted-foreground)]">{{ formatSize(file.size) }}</p>
                    </div>
                  </div>
                  <button 
                    @click="removeFile(index)" 
                    class="text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
                  >
                    <Icon name="heroicons:x-mark" class="w-5 h-5" />
                  </button>
                </div>
              </template>
            </draggable>
          </div>
        </client-only>

        <!-- Error Message -->
        <div v-if="error" class="alert-mono-error mt-6 flex items-start space-x-3">
          <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p class="text-sm">{{ error }}</p>
        </div>

        <!-- Success Message -->
        <div v-if="downloadUrl" class="alert-mono-success mt-6 text-center">
          <Icon name="heroicons:check-circle" class="w-12 h-12 mx-auto mb-4" />
          <p class="font-serif font-bold text-lg mb-4">PDF Merged Successfully!</p>
          <a 
            :href="downloadUrl" 
            download="merged.pdf"
            class="btn-mono-primary inline-flex"
          >
            <Icon name="heroicons:arrow-down-tray" class="w-4 h-4 mr-2" />
            Download Merged PDF
          </a>
        </div>
      </div>

      <!-- Action Button -->
      <div v-if="files.length > 1 && !downloadUrl" class="p-6 border-t-2 border-[var(--foreground)] bg-[var(--muted)]">
        <button 
          @click="mergePDFs" 
          :disabled="processing"
          class="btn-mono-primary w-full"
        >
          <span v-if="processing" class="flex items-center justify-center">
            <div class="w-4 h-4 border-2 border-[var(--background)]/30 border-t-[var(--background)] animate-spin mr-2"></div>
            Processing...
          </span>
          <span v-else class="flex items-center justify-center">
            <Icon name="heroicons:document-duplicate" class="w-4 h-4 mr-2" />
            Merge {{ files.length }} Files
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import draggable from 'vuedraggable'

definePageMeta({
  middleware: ['auth']
})

useHead({
  title: 'Merge PDF — LMAN Office Tools'
})

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const isDragging = ref(false)
const files = ref([])
const processing = ref(false)
const error = ref(null)
const downloadUrl = ref(null)

const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files)
  addFiles(selectedFiles)
}

const handleDrop = (event) => {
  isDragging.value = false
  const droppedFiles = Array.from(event.dataTransfer.files).filter(f => f.type === 'application/pdf')
  addFiles(droppedFiles)
}

const addFiles = (newFiles) => {
  error.value = null
  downloadUrl.value = null
  files.value = [...files.value, ...newFiles]
}

const removeFile = (index) => {
  files.value.splice(index, 1)
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const mergePDFs = async () => {
  if (files.value.length < 2) return
  
  processing.value = true
  error.value = null
  downloadUrl.value = null

  try {
    const formData = new FormData()
    files.value.forEach((file) => {
      formData.append('files', file)
    })

    const response = await fetch(`${apiBase}/api/v1/tools/merge-pdf`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Failed to merge PDFs')
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
