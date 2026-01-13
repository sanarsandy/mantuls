<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center">
        <NuxtLink to="/ocr" class="text-gray-400 hover:text-gray-600 mr-3">
          <Icon name="heroicons:arrow-left" class="w-5 h-5" />
        </NuxtLink>
        <h1 class="text-xl font-bold text-gray-900">Extraction Result</h1>
      </div>
      <div class="flex space-x-2">
        <button 
          @click="copyToClipboard" 
          class="inline-flex items-center px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm transition"
        >
          <Icon name="heroicons:clipboard-document" class="w-4 h-4 mr-1.5" />
          Copy
        </button>
        <button 
          @click="downloadJSON" 
          class="inline-flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition"
        >
          <Icon name="heroicons:arrow-down-tray" class="w-4 h-4 mr-1.5" />
          Download
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="bg-white rounded-2xl shadow-sm p-12 text-center">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p class="text-gray-500">Loading result...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-50 rounded-2xl p-8 text-center">
      <Icon name="heroicons:exclamation-circle" class="w-12 h-12 text-red-400 mx-auto mb-3" />
      <p class="text-red-600">{{ error }}</p>
    </div>

    <!-- Result -->
    <div v-else class="bg-white rounded-2xl shadow-sm overflow-hidden">
      <!-- Stats Bar -->
      <div class="bg-gray-50 px-6 py-3 border-b flex items-center justify-between text-sm">
        <div class="flex items-center space-x-4">
          <span class="text-gray-500">
            <span class="font-medium text-gray-900">{{ result?.details?.length || 0 }}</span> text blocks
          </span>
          <!-- Provider Badge -->
          <span v-if="result?.provider" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <Icon name="heroicons:cpu-chip" class="w-3 h-3 mr-1" />
            {{ getProviderDisplayName(result.provider) }}
          </span>
        </div>
        <span class="text-gray-400 text-xs">ID: {{ taskId?.slice(0, 8) }}...</span>
      </div>

      <!-- Text Content -->
      <div class="p-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">Extracted Text</label>
        <textarea 
          v-model="result.raw_text"
          rows="20" 
          class="w-full border border-gray-200 rounded-xl p-4 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-50"
        ></textarea>
      </div>
    </div>

    <!-- Copy Toast -->
    <div 
      v-if="showCopied" 
      class="fixed bottom-6 right-6 bg-gray-900 text-white px-4 py-2 rounded-lg text-sm shadow-lg"
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
  title: 'Result - OCR Service'
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
