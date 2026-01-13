<template>
  <div class="max-w-2xl mx-auto">
    <!-- Back Button -->
    <NuxtLink 
      to="/tools/ocr" 
      class="inline-flex items-center text-sm uppercase tracking-widest text-[var(--muted-foreground)] hover:text-[var(--foreground)] mb-8 transition-colors duration-100"
    >
      <Icon name="heroicons:arrow-left" class="w-4 h-4 mr-2" />
      Back to OCR Scanner
    </NuxtLink>

    <!-- Main Card -->
    <div class="border-2 border-[var(--foreground)] bg-[var(--background)]">
      
      <!-- Header -->
      <div class="p-8 border-b-2 border-[var(--foreground)]">
        <h1 class="font-serif text-3xl font-bold tracking-tighter">
          Scan Document
        </h1>
        <p class="text-[var(--muted-foreground)] mt-1">
          Supported formats: PDF, JPG, PNG
        </p>
      </div>

      <div class="p-8 space-y-8">
        
        <!-- API Key Selector -->
        <div class="border border-[var(--border-light)] p-6">
          <label class="label-mono flex items-center mb-3">
            <Icon name="heroicons:key" class="w-4 h-4 mr-2" />
            API Key (for testing prompts)
          </label>
          <select 
            v-model="selectedKeyId"
            class="select-mono"
          >
            <option value="">No API Key (auth disabled mode)</option>
            <option v-for="key in apiKeys" :key="key.id" :value="key.id">
              {{ key.name }} {{ key.custom_prompt ? '(has prompt)' : '' }}
            </option>
          </select>
          
          <p v-if="selectedKeyPrompt" class="mt-3 text-sm font-mono text-[var(--muted-foreground)] border-l-2 border-[var(--foreground)] pl-3">
            {{ selectedKeyPrompt.substring(0, 80) }}{{ selectedKeyPrompt.length > 80 ? '...' : '' }}
          </p>
        </div>

        <!-- Upload Area -->
        <div 
          class="border-2 border-dashed border-[var(--foreground)] p-12 text-center cursor-pointer transition-colors duration-100"
          :class="{ 
            'bg-[var(--foreground)] text-[var(--background)]': isDragging,
            'hover:bg-[var(--muted)]': !isDragging && !isUploading
          }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="handleDrop"
          @click="$refs.fileInput.click()"
        >
          <div v-if="!isUploading">
            <!-- Upload Icon -->
            <div 
              class="inline-flex items-center justify-center w-16 h-16 border-2 mb-6 transition-colors duration-100"
              :class="isDragging ? 'border-[var(--background)]' : 'border-[var(--foreground)]'"
            >
              <Icon 
                name="heroicons:cloud-arrow-up" 
                class="w-8 h-8"
                :class="isDragging ? 'text-[var(--background)]' : 'text-[var(--muted-foreground)]'"
              />
            </div>
            
            <p class="font-serif text-lg font-medium mb-1">
              Drop file here or click to browse
            </p>
            <p class="text-sm" :class="isDragging ? 'text-[var(--background)]/70' : 'text-[var(--muted-foreground)]'">
              Maximum file size: 10MB
            </p>
          </div>

          <!-- Loading State -->
          <div v-else class="py-4">
            <div class="spinner-mono mx-auto mb-6"></div>
            <p class="font-serif text-lg font-medium">
              Processing document...
            </p>
            <p class="text-sm text-[var(--muted-foreground)] mt-1">
              This may take a few seconds
            </p>
          </div>
        </div>

        <input 
          ref="fileInput" 
          type="file" 
          class="hidden" 
          accept=".pdf,.jpg,.jpeg,.png"
          @change="handleFileSelect"
        />

        <!-- Error Message -->
        <div v-if="error" class="alert-mono-error flex items-start space-x-3">
          <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p class="text-sm">{{ error }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  middleware: ['auth']
})

useHead({
  title: 'Scan — OCR Scanner'
})

const router = useRouter()
const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const isDragging = ref(false)
const isUploading = ref(false)
const error = ref(null)

// API Keys state
const apiKeys = ref([])
const selectedKeyId = ref('')

const selectedKeyPrompt = computed(() => {
  if (!selectedKeyId.value) return ''
  const key = apiKeys.value.find(k => k.id === selectedKeyId.value)
  return key?.custom_prompt || ''
})

onMounted(async () => {
  await loadApiKeys()
})

const loadApiKeys = async () => {
  try {
    const response = await fetch(`${apiBase}/api/v1/auth/keys`)
    const data = await response.json()
    apiKeys.value = (data.keys || []).filter(k => k.is_active)
  } catch (err) {
    console.error('Failed to load API keys:', err)
  }
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) processFile(file)
}

const handleDrop = (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file) processFile(file)
}

const processFile = async (file) => {
  error.value = null
  isUploading.value = true

  const formData = new FormData()
  formData.append('file', file)

  try {
    const headers = {}
    if (selectedKeyId.value) {
      headers['X-API-Key-ID'] = selectedKeyId.value
    }

    const response = await fetch(`${apiBase}/api/v1/ocr/upload`, {
      method: 'POST',
      headers,
      body: formData
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Upload failed')
    }

    const data = await response.json()
    const taskId = data.task_id
    
    await pollStatus(taskId)
  } catch (err) {
    console.error(err)
    error.value = err.message || 'An error occurred'
    isUploading.value = false
  }
}

const pollStatus = async (taskId) => {
  const maxAttempts = 60
  let attempts = 0

  const headers = {}
  if (selectedKeyId.value) {
    headers['X-API-Key-ID'] = selectedKeyId.value
  }

  const poll = async () => {
    try {
      const response = await fetch(`${apiBase}/api/v1/ocr/status/${taskId}`, { headers })
      const data = await response.json()

      if (data.status === 'completed') {
        if (selectedKeyId.value) {
          localStorage.setItem('ocr_api_key_id', selectedKeyId.value)
        }
        router.push(`/tools/ocr/result/${taskId}`)
      } else if (data.status === 'failed') {
        throw new Error('OCR processing failed')
      } else if (attempts < maxAttempts) {
        attempts++
        setTimeout(poll, 1000)
      } else {
        throw new Error('Processing timeout')
      }
    } catch (err) {
      error.value = err.message
      isUploading.value = false
    }
  }

  poll()
}
</script>
