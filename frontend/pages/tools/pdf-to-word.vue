<template>
  <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <NuxtLink to="/dashboard" class="text-[var(--muted-foreground)] hover:text-[var(--foreground)] flex items-center mb-2 text-sm transition-colors">
          <Icon name="heroicons:arrow-left" class="w-4 h-4 mr-1" />
          Back to Tools
        </NuxtLink>
        <h1 class="text-3xl font-serif font-bold tracking-tight">PDF to Word</h1>
        <p class="text-[var(--muted-foreground)] mt-2 font-mono text-sm max-w-2xl">
          Convert PDF documents to editable Word files (DOCX).
        </p>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      
      <!-- Upload Section -->
      <div class="lg:col-span-2 space-y-6">
        
        <!-- Input State -->
        <div class="card-mono p-8">
          <div 
            class="border-2 border-dashed border-[var(--border)] rounded-lg p-12 text-center hover:bg-[var(--accent)]/5 transition-colors cursor-pointer"
            :class="{ 'border-[var(--foreground)] bg-[var(--accent)]/5': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            @click="$refs.fileInput.click()"
          >
            <input 
              type="file" 
              ref="fileInput" 
              class="hidden" 
              accept="application/pdf" 
              @change="handleFileSelect"
            >
            
            <div class="space-y-4">
              <div class="w-16 h-16 bg-[var(--background)] border-2 border-[var(--foreground)] rounded-full flex items-center justify-center mx-auto mb-4">
                <Icon name="heroicons:document-text" class="w-8 h-8 text-[var(--foreground)]" />
              </div>
              <div v-if="!loading && !selectedFile">
                <h3 class="font-bold text-lg">Click to upload PDF</h3>
                <p class="text-[var(--muted-foreground)] text-sm font-mono">PDF files only (max 20MB)</p>
              </div>
              <div v-else-if="selectedFile && !loading" class="space-y-2">
                <p class="font-bold">{{ selectedFile.name }}</p>
                <p class="text-sm text-[var(--muted-foreground)]">{{ formatFileSize(selectedFile.size) }}</p>
              </div>
              <div v-if="loading" class="space-y-2">
                 <Icon name="heroicons:arrow-path" class="w-6 h-6 animate-spin mx-auto" />
                 <p class="text-sm font-mono">Converting to Word...</p>
                 <p class="text-xs text-[var(--muted-foreground)]">This may take a moment for large files.</p>
              </div>
            </div>
          </div>
          
          <!-- Convert Button -->
          <div v-if="selectedFile && !loading" class="mt-6 flex gap-4">
            <button @click="resetTool" class="btn-mono-outline flex-1">
              Change File
            </button>
            <button @click="convertPDF" class="btn-mono-primary flex-1 flex items-center justify-center">
              <Icon name="heroicons:arrow-path" class="w-5 h-5 mr-2" />
              Convert to Word
            </button>
          </div>
        </div>
        
        <!-- Error Message -->
        <div v-if="error" class="alert-mono-error flex items-center mt-4">
          <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 mr-2 flex-shrink-0" />
          <p class="text-sm font-mono">{{ error }}</p>
        </div>

      </div>

      <!-- Sidebar Info -->
      <div class="lg:col-span-1 space-y-6">
        <div class="card-mono p-6 bg-[var(--background)]">
          <h3 class="font-bold font-serif text-lg mb-4">About</h3>
          <ul class="space-y-4 text-sm text-[var(--muted-foreground)]">
            <li class="flex items-start">
              <Icon name="heroicons:check" class="w-4 h-4 mr-2 text-[var(--foreground)] flex-shrink-0 mt-0.5" />
              Converts PDF text and formatting to editable DOCX.
            </li>
            <li class="flex items-start">
              <Icon name="heroicons:check" class="w-4 h-4 mr-2 text-[var(--foreground)] flex-shrink-0 mt-0.5" />
              Works best with text-based PDFs (not scanned images).
            </li>
            <li class="flex items-start">
              <Icon name="heroicons:check" class="w-4 h-4 mr-2 text-[var(--foreground)] flex-shrink-0 mt-0.5" />
              Compatible with Microsoft Word, Google Docs, and LibreOffice.
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const selectedFile = ref(null)
const isDragging = ref(false)
const loading = ref(false)
const error = ref('')

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const handleDrop = (e) => {
  isDragging.value = false
  const droppedFile = e.dataTransfer.files[0]
  if (droppedFile && droppedFile.type === 'application/pdf') {
    selectedFile.value = droppedFile
    error.value = ''
  } else {
    error.value = 'Please upload a PDF file.'
  }
}

const handleFileSelect = (e) => {
  const file = e.target.files[0]
  if (file) {
    selectedFile.value = file
    error.value = ''
  }
}

const convertPDF = async () => {
  if (!selectedFile.value) return
  
  loading.value = true
  error.value = ''
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  
  try {
    const response = await fetch(`${apiBase}/api/v1/tools/pdf-to-word`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-API-Key': 'frontend-client',
      },
    })
    
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Conversion failed')
    }
    
    // Download the result
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = selectedFile.value.name.replace('.pdf', '.docx')
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    // Reset after success
    selectedFile.value = null
    
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Failed to convert PDF. Please try again.'
  } finally {
    loading.value = false
  }
}

const resetTool = () => {
  selectedFile.value = null
  error.value = ''
}
</script>
