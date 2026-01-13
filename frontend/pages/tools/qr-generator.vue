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
        QR CODE GENERATOR
      </h1>
      <p class="text-[var(--muted-foreground)] mt-2 text-lg">
        Generate QR codes for links, text, or data
      </p>
    </div>

    <!-- Main Content -->
    <div class="grid md:grid-cols-2 gap-8">
      
      <!-- Input Section -->
      <div class="border-2 border-[var(--foreground)] bg-[var(--background)]">
        <div class="p-6 border-b border-[var(--border-light)]">
          <label class="label-mono">Content Type</label>
          <div class="grid grid-cols-3 gap-2 mt-3">
            <button 
              v-for="type in contentTypes" 
              :key="type.value"
              @click="contentType = type.value"
              class="p-3 border-2 text-sm transition-colors"
              :class="contentType === type.value 
                ? 'border-[var(--foreground)] bg-[var(--foreground)] text-[var(--background)]' 
                : 'border-[var(--border-light)] hover:border-[var(--foreground)]'"
            >
              {{ type.label }}
            </button>
          </div>
        </div>

        <div class="p-6">
          <!-- URL Input -->
          <div v-if="contentType === 'url'">
            <label class="label-mono mb-2">Website URL</label>
            <input 
              v-model="content"
              type="url"
              placeholder="https://example.com"
              class="input-mono-bordered"
            />
          </div>

          <!-- Text Input -->
          <div v-if="contentType === 'text'">
            <label class="label-mono mb-2">Text Content</label>
            <textarea 
              v-model="content"
              rows="4"
              placeholder="Enter your text here..."
              class="input-mono-bordered resize-none"
            ></textarea>
          </div>

          <!-- WiFi Input -->
          <div v-if="contentType === 'wifi'" class="space-y-4">
            <div>
              <label class="label-mono mb-2">Network Name (SSID)</label>
              <input 
                v-model="wifiSSID"
                type="text"
                placeholder="My WiFi Network"
                class="input-mono-bordered"
              />
            </div>
            <div>
              <label class="label-mono mb-2">Password</label>
              <input 
                v-model="wifiPassword"
                type="text"
                placeholder="WiFi password"
                class="input-mono-bordered"
              />
            </div>
            <div>
              <label class="label-mono mb-2">Security Type</label>
              <select v-model="wifiSecurity" class="select-mono">
                <option value="WPA">WPA/WPA2</option>
                <option value="WEP">WEP</option>
                <option value="nopass">No Password</option>
              </select>
            </div>
          </div>

          <!-- QR Options -->
          <div class="mt-6 pt-6 border-t border-[var(--border-light)]">
            <label class="label-mono mb-3">QR Code Size</label>
            <select v-model="size" class="select-mono">
              <option value="200">Small (200px)</option>
              <option value="300">Medium (300px)</option>
              <option value="400">Large (400px)</option>
              <option value="500">Extra Large (500px)</option>
            </select>
          </div>

          <!-- Generate Button -->
          <button 
            @click="generateQR" 
            :disabled="!canGenerate || processing"
            class="btn-mono-primary w-full mt-6"
          >
            <span v-if="processing" class="flex items-center justify-center">
              <div class="w-4 h-4 border-2 border-[var(--background)]/30 border-t-[var(--background)] animate-spin mr-2"></div>
              Generating...
            </span>
            <span v-else class="flex items-center justify-center">
              <Icon name="heroicons:qr-code" class="w-4 h-4 mr-2" />
              Generate QR Code
            </span>
          </button>
        </div>
      </div>

      <!-- Preview Section -->
      <div class="border-2 border-[var(--foreground)] bg-[var(--background)]">
        <div class="p-6 border-b border-[var(--border-light)]">
          <label class="label-mono">Preview</label>
        </div>
        
        <div class="p-8 flex items-center justify-center min-h-[350px]">
          <!-- Empty State -->
          <div v-if="!qrImageUrl" class="text-center">
            <div class="inline-flex items-center justify-center w-20 h-20 border-2 border-[var(--border-light)] mb-4">
              <Icon name="heroicons:qr-code" class="w-10 h-10 text-[var(--muted-foreground)]" />
            </div>
            <p class="text-[var(--muted-foreground)] text-sm">
              Enter content and click Generate
            </p>
          </div>

          <!-- QR Code Result -->
          <div v-else class="text-center">
            <div class="border-2 border-[var(--foreground)] p-4 bg-white inline-block mb-6">
              <img :src="qrImageUrl" alt="QR Code" class="max-w-full" />
            </div>
            
            <div class="flex gap-3 justify-center">
              <a 
                :href="qrImageUrl" 
                :download="`qrcode-${Date.now()}.png`"
                class="btn-mono-primary"
              >
                <Icon name="heroicons:arrow-down-tray" class="w-4 h-4 mr-2" />
                Download PNG
              </a>
            </div>
          </div>
        </div>

        <!-- Error -->
        <div v-if="error" class="p-6 border-t border-[var(--border-light)]">
          <div class="alert-mono-error flex items-start space-x-3">
            <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 flex-shrink-0" />
            <p class="text-sm">{{ error }}</p>
          </div>
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
  title: 'QR Code Generator — LMAN Office Tools'
})

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const contentTypes = [
  { value: 'url', label: 'URL' },
  { value: 'text', label: 'Text' },
  { value: 'wifi', label: 'WiFi' }
]

const contentType = ref('url')
const content = ref('')
const wifiSSID = ref('')
const wifiPassword = ref('')
const wifiSecurity = ref('WPA')
const size = ref('300')
const processing = ref(false)
const error = ref(null)
const qrImageUrl = ref(null)

const canGenerate = computed(() => {
  if (contentType.value === 'wifi') {
    return wifiSSID.value.trim().length > 0
  }
  return content.value.trim().length > 0
})

const generateQR = async () => {
  processing.value = true
  error.value = null
  qrImageUrl.value = null

  try {
    let qrContent = content.value

    // Format WiFi string
    if (contentType.value === 'wifi') {
      qrContent = `WIFI:T:${wifiSecurity.value};S:${wifiSSID.value};P:${wifiPassword.value};;`
    }

    const response = await fetch(`${apiBase}/api/v1/tools/qr-generator`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: qrContent,
        size: parseInt(size.value)
      })
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Failed to generate QR code')
    }

    const blob = await response.blob()
    qrImageUrl.value = URL.createObjectURL(blob)
  } catch (err) {
    error.value = err.message
  } finally {
    processing.value = false
  }
}
</script>
