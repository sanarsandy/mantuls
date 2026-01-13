<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center">
        <NuxtLink to="/tools/ocr" class="text-[var(--muted-foreground)] hover:text-[var(--foreground)] mr-3 transition-colors">
          <Icon name="heroicons:arrow-left" class="w-5 h-5" />
        </NuxtLink>
        <h1 class="font-serif text-2xl font-bold tracking-tight">Extraction Result</h1>
      </div>
      <div class="flex space-x-3">
        <button 
          @click="copyToClipboard" 
          class="btn-mono-outline text-sm py-2 px-4"
        >
          <Icon name="heroicons:clipboard-document" class="w-4 h-4 mr-2" />
          Copy
        </button>
        <button 
          @click="downloadJSON" 
          class="btn-mono-primary text-sm py-2 px-4"
        >
          <Icon name="heroicons:arrow-down-tray" class="w-4 h-4 mr-2" />
          Download
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="border-2 border-[var(--foreground)] p-16 text-center">
      <div class="spinner-mono mx-auto mb-4"></div>
      <p class="text-[var(--muted-foreground)]">Loading result...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="alert-mono-error text-center p-8">
      <Icon name="heroicons:exclamation-circle" class="w-12 h-12 mx-auto mb-3" />
      <p>{{ error }}</p>
    </div>

    <!-- Result -->
    <div v-else class="border-2 border-[var(--foreground)]">
      <!-- Stats Bar -->
      <div class="bg-[var(--muted)] px-6 py-3 border-b-2 border-[var(--foreground)] flex items-center justify-between text-sm">
        <div class="flex items-center space-x-4">
          <span class="text-[var(--muted-foreground)]">
            <span class="font-bold text-[var(--foreground)]">{{ result?.details?.length || 0 }}</span> text blocks
          </span>
          <!-- Provider Badge -->
          <span v-if="result?.provider" class="badge-mono">
            <Icon name="heroicons:cpu-chip" class="w-3 h-3 mr-1" />
            {{ getProviderDisplayName(result.provider) }}
          </span>
        </div>
        <span class="text-[var(--muted-foreground)] text-xs font-mono">ID: {{ taskId?.slice(0, 8) }}...</span>
      </div>

      <!-- Text Content -->
      <div class="p-6">
        <label class="label-mono">Extracted Text</label>
        <textarea 
          v-model="result.raw_text"
          rows="20" 
          class="input-mono-bordered resize-none font-mono text-sm"
        ></textarea>
      </div>
    </div>

    <!-- Copy Toast -->
    <div 
      v-if="showCopied" 
      class="fixed bottom-6 right-6 bg-[var(--foreground)] text-[var(--background)] px-4 py-2 text-sm font-mono"
    >
      Copied to clipboard!
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  middleware: ['auth']
})

useHead({
  title: 'Result — OCR Scanner'
})

const route = useRoute()
const config = useRuntimeConfig()
const taskId = route.params.id
const apiBase = config.public.apiBase || 'http://localhost:8000'

const loading = ref(true)
const error = ref(null)
const result = ref({ raw_text: '', details: [] })
const showCopied = ref(false)

onMounted(async () => {
  try {
    // Get API key ID from localStorage (set by scan page)
    const apiKeyId = localStorage.getItem('ocr_api_key_id')
    const headers = {}
    if (apiKeyId) {
      headers['X-API-Key-ID'] = apiKeyId
    }

    const response = await fetch(`${apiBase}/api/v1/ocr/result/${taskId}`, { headers })
    if (!response.ok) throw new Error('Failed to fetch result')
    
    const data = await response.json()
    result.value = data.data || { raw_text: '', details: [] }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
})

const copyToClipboard = async () => {
  await navigator.clipboard.writeText(result.value.raw_text)
  showCopied.value = true
  setTimeout(() => showCopied.value = false, 2000)
}

const downloadJSON = () => {
  const blob = new Blob([JSON.stringify(result.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `ocr-result-${taskId}.json`
  a.click()
  URL.revokeObjectURL(url)
}

const getProviderDisplayName = (provider) => {
  const names = {
    'paddle_ocr': 'PaddleOCR',
    'google_vision': 'Google Vision',
    'mistral_ocr': 'Mistral AI',
    'groq_vision': 'Groq AI'
  }
  return names[provider] || provider
}
</script>
