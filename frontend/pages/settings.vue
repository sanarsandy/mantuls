<template>
  <div>
    <!-- Page Header -->
    <div class="mb-8 pb-8 border-b-4 border-[var(--foreground)]">
      <h1 class="font-serif text-4xl md:text-5xl font-bold tracking-tighter">
        SETTINGS
      </h1>
      <p class="text-[var(--muted-foreground)] mt-2 text-lg">
        Configure OCR provider and API access
      </p>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="border-2 border-[var(--foreground)] p-16 text-center">
      <div class="spinner-mono mx-auto"></div>
    </div>

    <!-- Settings Form -->
    <div v-else class="space-y-8">
      
      <!-- API Keys Section -->
      <section class="border-2 border-[var(--foreground)]">
        <div class="p-6 border-b-2 border-[var(--foreground)] flex flex-col md:flex-row md:justify-between md:items-center gap-4">
          <div>
            <h2 class="font-serif text-2xl font-bold tracking-tight">Api Keys</h2>
            <p class="text-sm text-[var(--muted-foreground)] mt-1">
              API keys are required for external applications
            </p>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm uppercase tracking-widest font-mono">Authentication</span>
            <button 
              @click="toggleAuth"
              class="toggle-mono"
              :class="{ 'active': authEnabled }"
              :aria-pressed="authEnabled"
            ></button>
          </div>
        </div>

        <div class="p-6 space-y-6">
          <!-- Create New Key -->
          <div class="border border-[var(--border-light)] p-6">
            <h3 class="label-mono mb-4">Create New API Key</h3>
            <div class="flex flex-col sm:flex-row gap-3">
              <input 
                v-model="newKeyName"
                type="text"
                placeholder="Key name (e.g., my-app)"
                class="input-mono-bordered flex-1"
              />
              <button 
                @click="createKey"
                :disabled="!newKeyName || creatingKey"
                class="btn-mono-primary whitespace-nowrap"
              >
                Create Key
              </button>
            </div>
          </div>

          <!-- New Key Display -->
          <div v-if="newlyCreatedKey" class="border-2 border-[var(--foreground)] bg-[var(--muted)] p-6">
            <div class="flex items-start space-x-4">
              <div class="w-10 h-10 border-2 border-[var(--foreground)] flex items-center justify-center flex-shrink-0">
                <Icon name="heroicons:key" class="w-5 h-5" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-serif font-bold text-lg">API Key Created!</p>
                <p class="text-sm text-[var(--muted-foreground)] mb-3">
                  Save this key now — it won't be shown again.
                </p>
                <div class="flex flex-col sm:flex-row gap-3">
                  <code class="flex-1 px-4 py-3 border-2 border-[var(--foreground)] bg-[var(--background)] font-mono text-sm break-all">
                    {{ newlyCreatedKey }}
                  </code>
                  <button @click="copyKey" class="btn-mono-outline whitespace-nowrap">
                    Copy
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- API Keys List -->
          <div class="space-y-4">
            <div 
              v-for="key in apiKeys" 
              :key="key.id"
              class="border p-6 transition-colors duration-100"
              :class="key.is_active 
                ? 'border-[var(--foreground)] hover:bg-[var(--muted)]' 
                : 'border-[var(--border-light)] bg-[var(--muted)] opacity-60'"
            >
              <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div class="flex items-start space-x-4">
                  <div class="w-10 h-10 border border-[var(--border-light)] flex items-center justify-center flex-shrink-0">
                    <Icon name="heroicons:key" class="w-5 h-5 text-[var(--muted-foreground)]" />
                  </div>
                  <div>
                    <p class="font-serif font-bold">{{ key.name }}</p>
                    <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs font-mono text-[var(--muted-foreground)] mt-1">
                      <span>{{ key.key_prefix }}</span>
                      <span>•</span>
                      <span>{{ formatDate(key.created_at) }}</span>
                      <span>•</span>
                      <span class="text-[var(--foreground)]">{{ key.request_count || 0 }} requests</span>
                      <span v-if="key.provider">•</span>
                      <span v-if="key.provider" class="badge-mono text-xs py-0">{{ key.provider }}</span>
                      <span v-if="key.custom_prompt">•</span>
                      <span v-if="key.custom_prompt" class="badge-mono-filled text-xs py-0">Has prompt</span>
                      <span v-if="!key.is_active">•</span>
                      <span v-if="!key.is_active" class="text-[var(--foreground)] font-bold">REVOKED</span>
                    </div>
                  </div>
                </div>
                <div class="flex space-x-2" v-if="key.is_active">
                  <button 
                    @click="openPromptEditor(key)" 
                    class="btn-mono-ghost text-sm"
                  >
                    <Icon name="heroicons:pencil" class="w-4 h-4" />
                    <span>Prompt</span>
                  </button>
                  <button 
                    @click="revokeKey(key.id)" 
                    class="btn-mono-ghost text-sm hover:text-red-600"
                  >
                    Revoke
                  </button>
                </div>
              </div>
              
              <!-- Prompt Preview -->
              <div v-if="key.custom_prompt" class="mt-4 p-3 border-l-2 border-[var(--foreground)] bg-[var(--muted)] font-mono text-xs text-[var(--muted-foreground)]">
                {{ key.custom_prompt.substring(0, 100) }}{{ key.custom_prompt.length > 100 ? '...' : '' }}
              </div>
            </div>
            
            <div v-if="apiKeys.length === 0" class="text-center py-12 text-[var(--muted-foreground)]">
              <p class="font-serif text-lg">No API keys yet</p>
              <p class="text-sm mt-1">Create one above to get started</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Prompt Editor Modal -->
      <div v-if="editingKey" class="modal-backdrop" @click.self="editingKey = null">
        <div class="modal-content">
          <div class="p-6 border-b-2 border-[var(--foreground)]">
            <h3 class="font-serif text-xl font-bold">Edit Prompt for "{{ editingKey.name }}"</h3>
            <p class="text-sm text-[var(--muted-foreground)] mt-1">
              Custom prompt will be used when this API key calls AI-powered OCR providers
            </p>
            <div class="mt-3 p-3 border-l-2 border-[var(--foreground)] bg-[var(--muted)] text-sm">
              <Icon name="heroicons:exclamation-triangle" class="w-4 h-4 inline mr-2" />
              Custom prompts only work with AI providers (Groq, Mistral). PaddleOCR and Google Vision use standard text extraction.
            </div>
          </div>
          
          <div class="p-6 space-y-6">
            <!-- Provider Selection -->
            <div>
              <label class="label-mono">OCR Provider</label>
              <select v-model="editForm.provider" class="select-mono">
                <option value="">Use Global Active Provider</option>
                <option v-for="p in availableProviders" :key="p.name" :value="p.name">
                  {{ p.display_name }}
                </option>
              </select>
              <p class="text-xs text-[var(--muted-foreground)] mt-2">
                Leave empty to use the global active provider
              </p>
            </div>
            
            <!-- Output Format -->
            <div>
              <label class="label-mono">Output Format</label>
              <div class="flex space-x-6 mt-2">
                <label class="flex items-center cursor-pointer">
                  <input 
                    type="radio" 
                    v-model="editForm.output_format" 
                    value="text" 
                    class="w-4 h-4 border-2 border-[var(--foreground)] appearance-none checked:bg-[var(--foreground)]"
                  />
                  <span class="ml-2">Text</span>
                </label>
                <label class="flex items-center cursor-pointer">
                  <input 
                    type="radio" 
                    v-model="editForm.output_format" 
                    value="json"
                    class="w-4 h-4 border-2 border-[var(--foreground)] appearance-none checked:bg-[var(--foreground)]"
                  />
                  <span class="ml-2">JSON</span>
                </label>
              </div>
            </div>
            
            <!-- Custom Prompt -->
            <div>
              <label class="label-mono">Custom Prompt</label>
              <textarea 
                v-model="editForm.custom_prompt"
                rows="6"
                placeholder="Extract all text from this image and return as JSON with fields: {invoice_number, vendor, date, items: [{description, qty, price}], total}"
                class="input-mono-bordered resize-none"
              ></textarea>
              <p class="text-xs text-[var(--muted-foreground)] mt-2">
                Leave empty to use default extraction prompt
              </p>
            </div>
            
            <!-- Example Prompts -->
            <div class="border border-[var(--border-light)] p-4">
              <p class="label-mono mb-3">Example Prompts</p>
              <div class="space-y-2 text-sm">
                <p 
                  class="cursor-pointer hover:text-[var(--muted-foreground)] transition-colors" 
                  @click="editForm.custom_prompt = 'Extract invoice data and return as JSON: {invoice_number, vendor_name, date, line_items: [{description, quantity, unit_price, total}], subtotal, tax, grand_total}'"
                >
                  → Invoice extraction (JSON)
                </p>
                <p 
                  class="cursor-pointer hover:text-[var(--muted-foreground)] transition-colors" 
                  @click="editForm.custom_prompt = 'Extract all text from this receipt. Return: store name, date, items purchased with prices, and total amount'"
                >
                  → Receipt extraction
                </p>
                <p 
                  class="cursor-pointer hover:text-[var(--muted-foreground)] transition-colors" 
                  @click="editForm.custom_prompt = 'Extract the ID card information as JSON: {name, id_number, date_of_birth, address, expiry_date}'"
                >
                  → ID Card extraction (JSON)
                </p>
              </div>
            </div>
          </div>
          
          <div class="p-6 border-t-2 border-[var(--foreground)] flex justify-end space-x-3 bg-[var(--muted)]">
            <button @click="editingKey = null" class="btn-mono-outline">
              Cancel
            </button>
            <button @click="savePrompt" :disabled="savingPrompt" class="btn-mono-primary">
              {{ savingPrompt ? 'Saving...' : 'Save Prompt' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Active Provider Section -->
      <section class="border-2 border-[var(--foreground)]">
        <div class="p-6 border-b-2 border-[var(--foreground)]">
          <h2 class="font-serif text-2xl font-bold tracking-tight">OCR Provider</h2>
        </div>
        
        <div class="p-6 space-y-4">
          <div 
            v-for="provider in availableProviders" 
            :key="provider.name"
            @click="selectProvider(provider.name)"
            class="flex items-center justify-between p-6 border cursor-pointer transition-all duration-100"
            :class="activeProvider === provider.name 
              ? 'border-[var(--foreground)] border-2 bg-[var(--foreground)] text-[var(--background)]' 
              : 'border-[var(--border-light)] hover:border-[var(--foreground)]'"
          >
            <div class="flex items-center space-x-4">
              <div 
                class="w-12 h-12 flex items-center justify-center border-2 transition-colors duration-100"
                :class="activeProvider === provider.name 
                  ? 'border-[var(--background)]' 
                  : 'border-[var(--foreground)]'"
              >
                <Icon 
                  :name="getProviderIcon(provider.name)" 
                  class="w-6 h-6"
                  :class="activeProvider === provider.name ? 'text-[var(--background)]' : 'text-[var(--foreground)]'"
                />
              </div>
              <div>
                <p class="font-serif font-bold text-lg">{{ provider.display_name }}</p>
                <p 
                  class="text-sm"
                  :class="activeProvider === provider.name ? 'text-[var(--background)]/70' : 'text-[var(--muted-foreground)]'"
                >
                  {{ provider.requires_api_key ? 'Requires API Key' : 'Free / Local' }}
                </p>
              </div>
            </div>
            <div 
              v-if="activeProvider === provider.name" 
              class="w-8 h-8 border-2 border-[var(--background)] flex items-center justify-center"
            >
              <Icon name="heroicons:check" class="w-5 h-5 text-[var(--background)]" />
            </div>
          </div>
        </div>
      </section>

      <!-- Provider Configuration -->
      <section v-if="currentProviderConfig" class="border-2 border-[var(--foreground)]">
        <div class="p-6 border-b-2 border-[var(--foreground)]">
          <h2 class="font-serif text-2xl font-bold tracking-tight">Provider Configuration</h2>
        </div>
        
        <div class="p-6 space-y-6">
          <!-- Language -->
          <div v-if="providerSettings.lang !== undefined">
            <label class="label-mono">Language Model</label>
            <select v-model="providerSettings.lang" class="select-mono">
              <option value="en">English</option>
              <option value="latin">Latin (ID/EN Mix)</option>
              <option value="ch">Chinese</option>
              <option value="japan">Japanese</option>
              <option value="korean">Korean</option>
            </select>
          </div>
          
          <!-- API Key -->
          <div v-if="currentProviderConfig.requires_api_key">
            <label class="label-mono">Provider API Key</label>
            <input 
              v-model="providerSettings.api_key" 
              type="password" 
              placeholder="Enter provider API key" 
              class="input-mono-bordered"
            />
          </div>
          
          <!-- GPU Toggle -->
          <div v-if="providerSettings.use_gpu !== undefined" class="flex items-center justify-between p-6 border border-[var(--border-light)]">
            <div>
              <p class="font-serif font-bold">Use GPU Acceleration</p>
              <p class="text-sm text-[var(--muted-foreground)]">Enable if GPU is available</p>
            </div>
            <button 
              @click="providerSettings.use_gpu = !providerSettings.use_gpu" 
              class="toggle-mono"
              :class="{ 'active': providerSettings.use_gpu }"
            ></button>
          </div>
        </div>
      </section>

      <!-- Save Button -->
      <button 
        @click="saveSettings" 
        :disabled="saving" 
        class="btn-mono-primary w-full"
      >
        {{ saving ? 'Saving...' : 'Save Provider Settings' }}
        <Icon v-if="!saving" name="heroicons:arrow-right" class="w-4 h-4 ml-2" />
      </button>

      <!-- Success Message -->
      <div v-if="showSuccess" class="alert-mono-success text-center">
        <p class="font-serif font-bold">Settings saved successfully!</p>
      </div>
    </div>
  </div>
</template>

<script setup>
definePageMeta({ middleware: ['auth'] })
useHead({ title: 'Settings — OCR Service' })

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const loading = ref(true)
const saving = ref(false)
const showSuccess = ref(false)

// Provider state
const activeProvider = ref('paddle_ocr')
const availableProviders = ref([])
const providerSettings = ref({})

// API Keys state
const apiKeys = ref([])
const authEnabled = ref(false)
const newKeyName = ref('')
const creatingKey = ref(false)
const newlyCreatedKey = ref(null)

// Prompt editor state
const editingKey = ref(null)
const editForm = ref({ custom_prompt: '', output_format: 'text' })
const savingPrompt = ref(false)

const currentProviderConfig = computed(() => availableProviders.value.find(p => p.name === activeProvider.value))

onMounted(async () => {
  await Promise.all([loadSettings(), loadApiKeys()])
})

const loadSettings = async () => {
  try {
    const response = await fetch(`${apiBase}/api/v1/settings`)
    const data = await response.json()
    activeProvider.value = data.active_provider
    availableProviders.value = data.available_providers
    providerSettings.value = data.providers[activeProvider.value] || {}
  } catch (err) {
    console.error('Failed to load settings:', err)
  } finally {
    loading.value = false
  }
}

const loadApiKeys = async () => {
  try {
    const response = await fetch(`${apiBase}/api/v1/auth/keys`)
    const data = await response.json()
    apiKeys.value = data.keys || []
    authEnabled.value = data.auth_enabled
  } catch (err) {
    console.error('Failed to load API keys:', err)
  }
}

const selectProvider = async (name) => {
  activeProvider.value = name
  try {
    const response = await fetch(`${apiBase}/api/v1/settings`)
    const data = await response.json()
    providerSettings.value = data.providers[name] || {}
  } catch (err) {
    console.error('Failed to load provider settings:', err)
  }
}

const saveSettings = async () => {
  saving.value = true
  showSuccess.value = false
  try {
    const response = await fetch(`${apiBase}/api/v1/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active_provider: activeProvider.value, providers: { [activeProvider.value]: providerSettings.value } })
    })
    if (response.ok) {
      showSuccess.value = true
      setTimeout(() => showSuccess.value = false, 3000)
    }
  } catch (err) {
    console.error('Failed to save settings:', err)
  } finally {
    saving.value = false
  }
}

const createKey = async () => {
  if (!newKeyName.value) return
  creatingKey.value = true
  newlyCreatedKey.value = null
  try {
    const response = await fetch(`${apiBase}/api/v1/auth/keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newKeyName.value })
    })
    const data = await response.json()
    if (data.key) {
      newlyCreatedKey.value = data.key.api_key
      newKeyName.value = ''
      await loadApiKeys()
    }
  } catch (err) {
    console.error('Failed to create API key:', err)
  } finally {
    creatingKey.value = false
  }
}

const revokeKey = async (keyId) => {
  if (!confirm('Are you sure you want to revoke this API key?')) return
  try {
    await fetch(`${apiBase}/api/v1/auth/keys/${keyId}/revoke`, { method: 'POST' })
    await loadApiKeys()
  } catch (err) {
    console.error('Failed to revoke API key:', err)
  }
}

const toggleAuth = async () => {
  try {
    await fetch(`${apiBase}/api/v1/auth/toggle`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: !authEnabled.value })
    })
    authEnabled.value = !authEnabled.value
  } catch (err) {
    console.error('Failed to toggle auth:', err)
  }
}

const openPromptEditor = (key) => {
  editingKey.value = key
  editForm.value = {
    custom_prompt: key.custom_prompt || '',
    output_format: key.output_format || 'text',
    provider: key.provider || ''
  }
}

const savePrompt = async () => {
  if (!editingKey.value) return
  savingPrompt.value = true
  try {
    await fetch(`${apiBase}/api/v1/auth/keys/${editingKey.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(editForm.value)
    })
    await loadApiKeys()
    editingKey.value = null
  } catch (err) {
    console.error('Failed to save prompt:', err)
  } finally {
    savingPrompt.value = false
  }
}

const copyKey = async () => {
  if (newlyCreatedKey.value) await navigator.clipboard.writeText(newlyCreatedKey.value)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
}

const getProviderIcon = (name) => {
  const icons = { 'paddle_ocr': 'heroicons:cpu-chip', 'google_vision': 'heroicons:cloud', 'mistral_ocr': 'heroicons:sparkles', 'groq_vision': 'heroicons:bolt' }
  return icons[name] || 'heroicons:cog-6-tooth'
}
</script>
