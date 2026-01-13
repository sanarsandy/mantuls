<template>
  <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <NuxtLink to="/dashboard" class="text-[var(--muted-foreground)] hover:text-[var(--foreground)] flex items-center mb-2 text-sm transition-colors">
          <Icon name="heroicons:arrow-left" class="w-4 h-4 mr-1" />
          Back to Tools
        </NuxtLink>
        <h1 class="text-3xl font-serif font-bold tracking-tight">Remove Background</h1>
        <p class="text-[var(--muted-foreground)] mt-2 font-mono text-sm max-w-2xl">
          Automatically remove background from photos using AI technology.
        </p>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      
      <!-- Upload & Result Section -->
      <div class="lg:col-span-2 space-y-6">
        
        <!-- Input State -->
        <div v-if="!resultImage" class="card-mono p-8">
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
              accept="image/*" 
              @change="handleFileSelect"
            >
            
            <div class="space-y-4">
              <div class="w-16 h-16 bg-[var(--background)] border-2 border-[var(--foreground)] rounded-full flex items-center justify-center mx-auto mb-4">
                <Icon name="heroicons:camera" class="w-8 h-8 text-[var(--foreground)]" />
              </div>
              <div v-if="!loading">
                <h3 class="font-bold text-lg">Click to upload image</h3>
                <p class="text-[var(--muted-foreground)] text-sm font-mono">JPG, PNG, WEBP (max 10MB)</p>
              </div>
              <div v-else class="space-y-2">
                 <Icon name="heroicons:arrow-path" class="w-6 h-6 animate-spin mx-auto" />
                 <p class="text-sm font-mono">Processing image with AI...</p>
                 <p class="text-xs text-[var(--muted-foreground)]">First run may take a while.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Result State -->
        <div v-else class="space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
             <!-- Original -->
             <div class="card-mono p-4">
               <h3 class="text-sm font-bold mb-2 text-[var(--muted-foreground)]">Original</h3>
               <div class="aspect-square bg-[var(--muted)]/10 rounded-lg overflow-hidden flex items-center justify-center relative">
                  <img :src="originalImagePreview" class="max-w-full max-h-full object-contain" />
               </div>
             </div>
             
             <!-- Result -->
             <div class="card-mono p-4 border-[var(--foreground)]">
               <h3 class="text-sm font-bold mb-2 flex items-center justify-between">
                 <span>No Background</span>
                 <span class="text-xs px-2 py-0.5 bg-[var(--accent)] text-[var(--background)] rounded-full">AI Magic</span>
               </h3>
               <!-- Checkerboard pattern for transparency -->
               <div class="aspect-square rounded-lg overflow-hidden flex items-center justify-center relative"
                    style="background-image: linear-gradient(45deg, #ccc 25%, transparent 25%), linear-gradient(-45deg, #ccc 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #ccc 75%), linear-gradient(-45deg, transparent 75%, #ccc 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px;">
                  <img :src="resultImage" class="max-w-full max-h-full object-contain z-10" />
               </div>
             </div>
          </div>
          
          <div class="flex gap-4">
             <button @click="resetTool" class="btn-mono-outline flex-1">
               Process Another
             </button>
             <a :href="resultImage" download="nobg_image.png" class="btn-mono-primary flex-1 flex items-center justify-center">
               <Icon name="heroicons:arrow-down-tray" class="w-5 h-5 mr-2" />
               Download PNG
             </a>
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
          <h3 class="font-bold font-serif text-lg mb-4">Tips</h3>
          <ul class="space-y-4 text-sm text-[var(--muted-foreground)]">
            <li class="flex items-start">
              <Icon name="heroicons:check" class="w-4 h-4 mr-2 text-[var(--foreground)] flex-shrink-0 mt-0.5" />
              Use images with clear contrast between subject and background.
            </li>
            <li class="flex items-start">
              <Icon name="heroicons:check" class="w-4 h-4 mr-2 text-[var(--foreground)] flex-shrink-0 mt-0.5" />
              Works best on portraits, products, and distinct objects.
            </li>
            <li class="flex items-start">
              <Icon name="heroicons:check" class="w-4 h-4 mr-2 text-[var(--foreground)] flex-shrink-0 mt-0.5" />
              Result is always a PNG with transparency alpha channel.
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const originalImagePreview = ref(null)
const resultImage = ref(null)
const isDragging = ref(false)
const loading = ref(false)
const error = ref('')
const file = ref(null)

// Get API Base URL
const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const handleDrop = (e) => {
  isDragging.value = false
  const droppedFile = e.dataTransfer.files[0]
  if (droppedFile && droppedFile.type.startsWith('image/')) {
    processFile(droppedFile)
  } else {
    error.value = 'Please upload an image file.'
  }
}

const handleFileSelect = (e) => {
  const selectedFile = e.target.files[0]
  if (selectedFile) {
    processFile(selectedFile)
  }
}

const processFile = async (selectedFile) => {
  loading.value = true
  error.value = ''
  file.value = selectedFile
  
  // Create preview for original
  originalImagePreview.value = URL.createObjectURL(selectedFile)
  
  const formData = new FormData()
  formData.append('file', selectedFile)
  
  try {
    const { data, error: fetchError } = await useFetch(`${apiBase}/api/v1/tools/remove-bg`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-API-Key': 'frontend-client', 
      },
      responseType: 'blob' 
    })
    
    if (fetchError.value) throw new Error(fetchError.value.message || 'Failed to remove background')
    
    // Create URL for result
    const blob = new Blob([data.value], { type: 'image/png' })
    resultImage.value = URL.createObjectURL(blob)
    
  } catch (err) {
    console.error(err)
    error.value = 'Failed to process image. The AI service might be busy or starting up.'
    // Reset if failed
    originalImagePreview.value = null
    file.value = null
  } finally {
    loading.value = false
  }
}

const resetTool = () => {
    if (originalImagePreview.value) URL.revokeObjectURL(originalImagePreview.value)
    if (resultImage.value) URL.revokeObjectURL(resultImage.value)
    
    originalImagePreview.value = null
    resultImage.value = null
    file.value = null
    error.value = ''
}
</script>
