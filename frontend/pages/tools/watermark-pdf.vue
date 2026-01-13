<template>
  <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <NuxtLink to="/dashboard" class="text-[var(--muted-foreground)] hover:text-[var(--foreground)] flex items-center mb-2 text-sm transition-colors">
          <Icon name="heroicons:arrow-left" class="w-4 h-4 mr-1" />
          Back to Tools
        </NuxtLink>
        <h1 class="text-3xl font-serif font-bold tracking-tight">Watermark PDF</h1>
        <p class="text-[var(--muted-foreground)] mt-2 font-mono text-sm max-w-2xl">
          Add text watermark to your PDF documents.
        </p>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      
      <!-- Upload & Options Section -->
      <div class="lg:col-span-2 space-y-6">
        
        <!-- File Upload -->
        <div class="card-mono p-8">
          <h3 class="font-bold mb-4">1. Upload PDF</h3>
          <div 
            class="border-2 border-dashed border-[var(--border)] rounded-lg p-8 text-center hover:bg-[var(--accent)]/5 transition-colors cursor-pointer"
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
            
            <div v-if="!selectedFile">
              <Icon name="heroicons:document-plus" class="w-12 h-12 mx-auto mb-2 text-[var(--muted-foreground)]" />
              <p class="font-bold">Click to upload PDF</p>
              <p class="text-sm text-[var(--muted-foreground)]">or drag and drop</p>
            </div>
            <div v-else class="flex items-center justify-center gap-2">
              <Icon name="heroicons:document-check" class="w-6 h-6 text-green-600" />
              <span class="font-bold">{{ selectedFile.name }}</span>
              <button @click.stop="selectedFile = null" class="text-red-500 hover:text-red-700">
                <Icon name="heroicons:x-mark" class="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
        
        <!-- Watermark Options -->
        <div class="card-mono p-8">
          <h3 class="font-bold mb-4">2. Watermark Settings</h3>
          
          <div class="space-y-4">
            <!-- Watermark Text -->
            <div>
              <label class="block text-sm font-bold mb-2">Watermark Text</label>
              <input 
                v-model="watermarkText" 
                type="text" 
                class="w-full px-4 py-3 border-2 border-[var(--border)] bg-[var(--background)] focus:border-[var(--foreground)] outline-none transition-colors"
                placeholder="e.g., CONFIDENTIAL, DRAFT, SAMPLE"
              >
            </div>
            
            <!-- Position -->
            <div>
              <label class="block text-sm font-bold mb-2">Position</label>
              <div class="flex gap-4">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="radio" v-model="position" value="diagonal" class="w-4 h-4">
                  <span>Diagonal</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input type="radio" v-model="position" value="center" class="w-4 h-4">
                  <span>Center</span>
                </label>
              </div>
            </div>
            
            <!-- Opacity -->
            <div>
              <label class="block text-sm font-bold mb-2">Opacity: {{ Math.round(opacity * 100) }}%</label>
              <input 
                type="range" 
                v-model.number="opacity" 
                min="0.1" 
                max="1" 
                step="0.1"
                class="w-full"
              >
            </div>
          </div>
        </div>
        
        <!-- Apply Button -->
        <button 
          @click="applyWatermark" 
          :disabled="!selectedFile || !watermarkText || loading"
          class="w-full btn-mono-primary py-4 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Icon v-if="loading" name="heroicons:arrow-path" class="w-5 h-5 mr-2 animate-spin" />
          <Icon v-else name="heroicons:paint-brush" class="w-5 h-5 mr-2" />
          {{ loading ? 'Processing...' : 'Apply Watermark' }}
        </button>
        
        <!-- Error Message -->
        <div v-if="error" class="alert-mono-error flex items-center">
          <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 mr-2 flex-shrink-0" />
          <p class="text-sm font-mono">{{ error }}</p>
        </div>

      </div>

      <!-- Sidebar -->
      <div class="lg:col-span-1 space-y-6">
        <!-- Preview -->
        <div class="card-mono p-6 bg-[var(--background)]">
          <h3 class="font-bold font-serif text-lg mb-4">Preview</h3>
          <div class="aspect-[3/4] bg-white border-2 border-[var(--border)] rounded flex items-center justify-center relative overflow-hidden">
            <div class="absolute inset-0 flex items-center justify-center">
              <span 
                class="text-2xl font-bold text-gray-400 select-none"
                :class="{ 'rotate-45': position === 'diagonal' }"
                :style="{ opacity: opacity }"
              >
                {{ watermarkText || 'WATERMARK' }}
              </span>
            </div>
            <Icon name="heroicons:document" class="w-16 h-16 text-[var(--muted-foreground)]" />
          </div>
        </div>
        
        <!-- Tips -->
        <div class="card-mono p-6 bg-[var(--background)]">
          <h3 class="font-bold font-serif text-lg mb-4">Common Watermarks</h3>
          <div class="flex flex-wrap gap-2">
            <button 
              v-for="text in ['CONFIDENTIAL', 'DRAFT', 'SAMPLE', 'DO NOT COPY', 'INTERNAL']"
              :key="text"
              @click="watermarkText = text"
              class="px-3 py-1 text-xs border border-[var(--border)] hover:bg-[var(--accent)] transition-colors"
            >
              {{ text }}
            </button>
          </div>
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

const watermarkText = ref('')
const position = ref('diagonal')
const opacity = ref(0.3)

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

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

const applyWatermark = async () => {
  if (!selectedFile.value || !watermarkText.value) return
  
  loading.value = true
  error.value = ''
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('text', watermarkText.value)
  formData.append('position', position.value)
  formData.append('opacity', opacity.value.toString())
  
  try {
    const response = await fetch(`${apiBase}/api/v1/tools/watermark-pdf`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-API-Key': 'frontend-client',
      },
    })
    
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Failed to add watermark')
    }
    
    // Download the result
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `watermarked_${selectedFile.value.name}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
  } catch (err) {
    console.error(err)
    error.value = err.message || 'Failed to add watermark. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>
