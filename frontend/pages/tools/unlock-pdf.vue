<template>
  <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <NuxtLink to="/dashboard" class="text-[var(--muted-foreground)] hover:text-[var(--foreground)] flex items-center mb-2 text-sm transition-colors">
          <Icon name="heroicons:arrow-left" class="w-4 h-4 mr-1" />
          Back to Tools
        </NuxtLink>
        <h1 class="text-3xl font-serif font-bold tracking-tight">Unlock PDF</h1>
        <p class="text-[var(--muted-foreground)] mt-2 font-mono text-sm max-w-2xl">
          Remove password security from your PDF documents.
        </p>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      
      <!-- Upload & Form Section -->
      <div class="lg:col-span-2 space-y-6">
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
              accept=".pdf" 
              @change="handleFileSelect"
            >
            
            <div v-if="!file" class="space-y-4">
              <div class="w-16 h-16 bg-[var(--background)] border-2 border-[var(--foreground)] rounded-full flex items-center justify-center mx-auto mb-4">
                <Icon name="heroicons:lock-open" class="w-8 h-8 text-[var(--foreground)]" />
              </div>
              <h3 class="font-bold text-lg">Click to upload locked PDF</h3>
              <p class="text-[var(--muted-foreground)] text-sm font-mono">Drag & drop supported</p>
            </div>
            
            <div v-else class="space-y-4">
              <div class="w-16 h-16 bg-[var(--background)] border-2 border-[var(--foreground)] rounded-full flex items-center justify-center mx-auto mb-4">
                <Icon name="heroicons:document-text" class="w-8 h-8 text-[var(--foreground)]" />
              </div>
              <h3 class="font-bold text-lg">{{ file.name }}</h3>
              <p class="text-[var(--muted-foreground)] text-sm font-mono">{{ formatFileSize(file.size) }}</p>
              <button @click.stop="file = null" class="btn-mono-outline text-xs mt-2">
                Remove File
              </button>
            </div>
          </div>
        </div>

        <!-- Password Input -->
        <div class="card-mono p-6">
           <h3 class="font-bold font-serif text-lg mb-4 flex items-center">
             <Icon name="heroicons:key" class="w-5 h-5 mr-2" />
             Decryption
           </h3>
           
           <div class="space-y-4">
             <div>
               <label class="label-mono">Current Password</label>
               <input 
                 v-model="password" 
                 type="password" 
                 class="input-mono" 
                 placeholder="Enter the password to open this file"
               />
               <p class="text-xs text-[var(--muted-foreground)] mt-1">We need the password once to decrypt the file permanently.</p>
             </div>
           </div>
        </div>

        <!-- Action Button -->
        <button 
          @click="processFile"
          :disabled="!file || !password || loading"
          class="btn-mono-primary w-full py-4 text-lg"
        >
          <span v-if="loading" class="flex items-center justify-center space-x-2">
            <Icon name="heroicons:arrow-path" class="animate-spin w-5 h-5" />
            <span>Unlocking PDF...</span>
          </span>
          <span v-else class="flex items-center justify-center space-x-2">
            <Icon name="heroicons:lock-open" class="w-5 h-5" />
            <span>Unlock PDF Now</span>
          </span>
        </button>
        
        <!-- Error Message -->
         <div v-if="error" class="alert-mono-error flex items-center">
           <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 mr-2 flex-shrink-0" />
           <p class="text-sm font-mono">{{ error }}</p>
         </div>

      </div>

      <!-- Sidebar Info -->
      <div class="lg:col-span-1 space-y-6">
        <div class="card-mono p-6 bg-[var(--background)]">
          <h3 class="font-bold font-serif text-lg mb-4">How it works</h3>
          <ul class="space-y-4 text-sm text-[var(--muted-foreground)]">
            <li class="flex items-start">
              <span class="mr-2 text-[var(--foreground)] font-bold">1.</span>
              Upload a password-protected PDF.
            </li>
            <li class="flex items-start">
              <span class="mr-2 text-[var(--foreground)] font-bold">2.</span>
              Enter the correct password.
            </li>
            <li class="flex items-start">
              <span class="mr-2 text-[var(--foreground)] font-bold">3.</span>
              Download a new version of the PDF that has the password removed. Useful for archiving bank statements or payslips.
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const file = ref(null)
const password = ref('')
const isDragging = ref(false)
const loading = ref(false)
const error = ref('')

// Get API Base URL
const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const handleDrop = (e) => {
  isDragging.value = false
  const droppedFile = e.dataTransfer.files[0]
  if (droppedFile && droppedFile.type === 'application/pdf') {
    file.value = droppedFile
    error.value = ''
  } else {
    error.value = 'Please upload a PDF file.'
  }
}

const handleFileSelect = (e) => {
  const selectedFile = e.target.files[0]
  if (selectedFile) {
    file.value = selectedFile
    error.value = ''
  }
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const processFile = async () => {
  if (!file.value || !password.value) return
  
  loading.value = true
  error.value = ''
  
  const formData = new FormData()
  formData.append('file', file.value)
  formData.append('password', password.value)
  
  try {
    const { data, error: fetchError } = await useFetch(`${apiBase}/api/v1/tools/unlock-pdf`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-API-Key': 'frontend-client', 
      },
      responseType: 'blob' 
    })
    
    if (fetchError.value) {
      if (fetchError.value.statusCode === 400) {
        throw new Error('Incorrect password or invalid file.')
      }
      throw new Error(fetchError.value.message || 'Failed to unlock PDF')
    }
    
    // Create download link
    const blob = new Blob([data.value], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `unlocked_${file.value.name}`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    
  } catch (err) {
    console.error(err)
    error.value = err.message || 'An error occurred while processing your file.'
  } finally {
    loading.value = false
  }
}
</script>
