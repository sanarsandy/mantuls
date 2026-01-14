<template>
  <div class="max-w-4xl mx-auto">
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
        SIGN PDF
      </h1>
      <p class="text-[var(--muted-foreground)] mt-2 text-lg">
        Add your signature to PDF documents
      </p>
    </div>

    <!-- Main Content -->
    <div class="space-y-8">
      
      <!-- Step 1: Upload PDF -->
      <div class="border-2 border-[var(--foreground)] bg-[var(--background)]">
        <div class="p-4 border-b-2 border-[var(--foreground)] bg-[var(--muted)]">
          <h2 class="font-serif font-bold flex items-center">
            <span class="w-6 h-6 border-2 border-[var(--foreground)] flex items-center justify-center text-sm mr-3">1</span>
            Upload PDF
          </h2>
        </div>
        <div class="p-6">
          <div v-if="!pdfFile">
            <div 
              class="border-2 border-dashed border-[var(--foreground)] p-12 text-center cursor-pointer transition-colors duration-100"
              :class="{ 
                'bg-[var(--foreground)] text-[var(--background)]': isDragging,
                'hover:bg-[var(--muted)]': !isDragging
              }"
              @dragover.prevent="isDragging = true"
              @dragleave="isDragging = false"
              @drop.prevent="handlePdfDrop"
              @click="$refs.pdfInput.click()"
            >
              <div 
                class="inline-flex items-center justify-center w-14 h-14 border-2 mb-4 transition-colors duration-100"
                :class="isDragging ? 'border-[var(--background)]' : 'border-[var(--foreground)]'"
              >
                <Icon name="heroicons:document" class="w-7 h-7" />
              </div>
              <p class="font-serif font-medium mb-1">Drop PDF file here or click to browse</p>
              <p class="text-sm text-[var(--muted-foreground)]">Select a PDF to sign</p>
            </div>
            <input 
              ref="pdfInput" 
              type="file" 
              class="hidden" 
              accept=".pdf"
              @change="handlePdfSelect"
            />
          </div>
          
          <div v-else class="flex items-center justify-between p-4 border-2 border-[var(--foreground)]">
            <div class="flex items-center space-x-4">
              <div class="w-10 h-10 border-2 border-[var(--foreground)] flex items-center justify-center">
                <Icon name="heroicons:document" class="w-5 h-5" />
              </div>
              <div>
                <p class="font-medium">{{ pdfFile.name }}</p>
                <p class="text-xs text-[var(--muted-foreground)]">
                  {{ pdfInfo ? `${pdfInfo.page_count} page(s)` : 'Loading...' }}
                </p>
              </div>
            </div>
            <button @click="clearPdf" class="text-[var(--muted-foreground)] hover:text-[var(--foreground)]">
              <Icon name="heroicons:x-mark" class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      <!-- Step 2: Create Signature -->
      <div class="border-2 border-[var(--foreground)] bg-[var(--background)]" :class="{ 'opacity-50 pointer-events-none': !pdfFile }">
        <div class="p-4 border-b-2 border-[var(--foreground)] bg-[var(--muted)]">
          <h2 class="font-serif font-bold flex items-center">
            <span class="w-6 h-6 border-2 border-[var(--foreground)] flex items-center justify-center text-sm mr-3">2</span>
            Create Signature
          </h2>
        </div>
        <div class="p-6">
          <!-- Signature Mode Tabs -->
          <div class="flex border-2 border-[var(--foreground)] mb-4">
            <button
              @click="signatureMode = 'draw'"
              class="flex-1 py-2 px-4 text-sm font-medium transition-colors"
              :class="signatureMode === 'draw' ? 'bg-[var(--foreground)] text-[var(--background)]' : 'hover:bg-[var(--muted)]'"
            >
              <Icon name="heroicons:pencil" class="w-4 h-4 inline mr-2" />
              Draw
            </button>
            <button
              @click="signatureMode = 'upload'"
              class="flex-1 py-2 px-4 text-sm font-medium border-l-2 border-[var(--foreground)] transition-colors"
              :class="signatureMode === 'upload' ? 'bg-[var(--foreground)] text-[var(--background)]' : 'hover:bg-[var(--muted)]'"
            >
              <Icon name="heroicons:arrow-up-tray" class="w-4 h-4 inline mr-2" />
              Upload
            </button>
          </div>

          <!-- Draw Mode -->
          <div v-if="signatureMode === 'draw'" class="space-y-4">
            <div class="border-2 border-[var(--foreground)] bg-white">
              <canvas 
                ref="signatureCanvas"
                class="w-full h-40 cursor-crosshair touch-none"
                @mousedown="startDrawing"
                @mousemove="draw"
                @mouseup="stopDrawing"
                @mouseleave="stopDrawing"
                @touchstart.prevent="startDrawingTouch"
                @touchmove.prevent="drawTouch"
                @touchend="stopDrawing"
              ></canvas>
            </div>
            <div class="flex justify-between items-center">
              <button 
                @click="clearSignature"
                class="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] flex items-center"
              >
                <Icon name="heroicons:arrow-path" class="w-4 h-4 mr-1" />
                Clear
              </button>
              <div class="flex items-center space-x-3">
                <label class="text-sm text-[var(--muted-foreground)]">Color:</label>
                <input 
                  type="color" 
                  v-model="penColor" 
                  class="w-8 h-8 border-2 border-[var(--foreground)] cursor-pointer"
                />
              </div>
            </div>
          </div>

          <!-- Upload Mode -->
          <div v-if="signatureMode === 'upload'" class="space-y-4">
            <div v-if="!uploadedSignature">
              <div 
                class="border-2 border-dashed border-[var(--foreground)] p-8 text-center cursor-pointer hover:bg-[var(--muted)]"
                @click="$refs.sigInput.click()"
              >
                <Icon name="heroicons:photo" class="w-8 h-8 mx-auto mb-2 text-[var(--muted-foreground)]" />
                <p class="text-sm">Click to upload signature image</p>
                <p class="text-xs text-[var(--muted-foreground)]">PNG with transparent background recommended</p>
              </div>
              <input 
                ref="sigInput" 
                type="file" 
                class="hidden" 
                accept="image/png,image/jpeg,image/webp"
                @change="handleSignatureUpload"
              />
            </div>
            <div v-else class="text-center">
              <img :src="uploadedSignaturePreview" class="max-h-32 mx-auto border-2 border-[var(--foreground)]" />
              <button 
                @click="clearUploadedSignature"
                class="mt-2 text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 3: Position & Size -->
      <div class="border-2 border-[var(--foreground)] bg-[var(--background)]" :class="{ 'opacity-50 pointer-events-none': !hasSignature }">
        <div class="p-4 border-b-2 border-[var(--foreground)] bg-[var(--muted)]">
          <h2 class="font-serif font-bold flex items-center">
            <span class="w-6 h-6 border-2 border-[var(--foreground)] flex items-center justify-center text-sm mr-3">3</span>
            Position & Size
          </h2>
        </div>
        <div class="p-6 space-y-6">
          <!-- Page Selection -->
          <div v-if="pdfInfo && pdfInfo.page_count > 1" class="flex items-center space-x-4">
            <label class="label-mono">Page:</label>
            <select 
              v-model="selectedPage" 
              @change="loadPagePreview"
              class="input-mono flex-1"
            >
              <option v-for="p in pdfInfo.page_count" :key="p" :value="p">
                Page {{ p }}
              </option>
            </select>
          </div>

          <!-- Visual PDF Preview with Draggable Signature -->
          <div class="space-y-3">
            <label class="label-mono">Drag signature to position:</label>
            <div 
              ref="previewContainer"
              class="relative border-2 border-[var(--foreground)] bg-gray-100 overflow-hidden"
              :style="{ minHeight: '300px' }"
            >
              <!-- PDF Page Preview -->
              <img 
                v-if="pagePreviewUrl"
                :src="pagePreviewUrl"
                ref="previewImage"
                class="w-full h-auto"
                @load="onPreviewLoad"
              />
              
              <!-- Loading State -->
              <div v-else-if="loadingPreview" class="absolute inset-0 flex items-center justify-center">
                <div class="text-center">
                  <div class="w-8 h-8 border-2 border-[var(--foreground)]/30 border-t-[var(--foreground)] animate-spin mx-auto mb-2"></div>
                  <p class="text-sm text-[var(--muted-foreground)]">Loading preview...</p>
                </div>
              </div>

              <!-- Placeholder when no PDF -->
              <div v-else class="absolute inset-0 flex items-center justify-center text-[var(--muted-foreground)]">
                <p class="text-sm">Upload PDF to see preview</p>
              </div>

              <!-- Draggable & Resizable Signature Overlay -->
              <div 
                v-if="pagePreviewUrl && signaturePreviewUrl"
                ref="signatureOverlay"
                class="absolute cursor-move border-2 border-dashed border-blue-500 bg-white/80 overflow-hidden"
                :style="signatureOverlayStyle"
                @mousedown.self="startDrag"
                @touchstart.prevent.self="startDragTouch"
              >
                <img 
                  :src="signaturePreviewUrl" 
                  class="absolute pointer-events-none"
                  :style="signatureImageStyle"
                />
                
                <!-- Corner Handles -->
                <!-- Top-left -->
                <div 
                  class="absolute top-0 left-0 w-3 h-3 bg-blue-500 cursor-nw-resize -translate-x-1/2 -translate-y-1/2"
                  @mousedown.stop="(e) => startResize(e, 'nw')"
                  @touchstart.prevent.stop="(e) => startResizeTouch(e, 'nw')"
                ></div>
                <!-- Top-right -->
                <div 
                  class="absolute top-0 right-0 w-3 h-3 bg-blue-500 cursor-ne-resize translate-x-1/2 -translate-y-1/2"
                  @mousedown.stop="(e) => startResize(e, 'ne')"
                  @touchstart.prevent.stop="(e) => startResizeTouch(e, 'ne')"
                ></div>
                <!-- Bottom-left -->
                <div 
                  class="absolute bottom-0 left-0 w-3 h-3 bg-blue-500 cursor-sw-resize -translate-x-1/2 translate-y-1/2"
                  @mousedown.stop="(e) => startResize(e, 'sw')"
                  @touchstart.prevent.stop="(e) => startResizeTouch(e, 'sw')"
                ></div>
                <!-- Bottom-right -->
                <div 
                  class="absolute bottom-0 right-0 w-3 h-3 bg-blue-500 cursor-se-resize translate-x-1/2 translate-y-1/2"
                  @mousedown.stop="(e) => startResize(e, 'se')"
                  @touchstart.prevent.stop="(e) => startResizeTouch(e, 'se')"
                ></div>
                
                <!-- Edge Handles -->
                <!-- Top edge -->
                <div 
                  class="absolute top-0 left-1/2 w-6 h-2 bg-blue-400 cursor-n-resize -translate-x-1/2 -translate-y-1/2"
                  @mousedown.stop="(e) => startResize(e, 'n')"
                  @touchstart.prevent.stop="(e) => startResizeTouch(e, 'n')"
                ></div>
                <!-- Bottom edge -->
                <div 
                  class="absolute bottom-0 left-1/2 w-6 h-2 bg-blue-400 cursor-s-resize -translate-x-1/2 translate-y-1/2"
                  @mousedown.stop="(e) => startResize(e, 's')"
                  @touchstart.prevent.stop="(e) => startResizeTouch(e, 's')"
                ></div>
                <!-- Left edge -->
                <div 
                  class="absolute left-0 top-1/2 w-2 h-6 bg-blue-400 cursor-w-resize -translate-x-1/2 -translate-y-1/2"
                  @mousedown.stop="(e) => startResize(e, 'w')"
                  @touchstart.prevent.stop="(e) => startResizeTouch(e, 'w')"
                ></div>
                <!-- Right edge -->
                <div 
                  class="absolute right-0 top-1/2 w-2 h-6 bg-blue-400 cursor-e-resize translate-x-1/2 -translate-y-1/2"
                  @mousedown.stop="(e) => startResize(e, 'e')"
                  @touchstart.prevent.stop="(e) => startResizeTouch(e, 'e')"
                ></div>
              </div>
            </div>
            <p class="text-xs text-[var(--muted-foreground)]">
              <Icon name="heroicons:cursor-arrow-rays" class="w-4 h-4 inline" />
              Drag corners or edges to crop
            </p>
          </div>

          <!-- Size Sliders -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="label-mono">Width: {{ sigWidth }}px</label>
              <input 
                type="range" 
                v-model.number="sigWidth" 
                min="20" 
                :max="origSigWidth - cropLeft"
                class="w-full mt-1"
              />
            </div>
            <div>
              <label class="label-mono">Height: {{ sigHeight }}px</label>
              <input 
                type="range" 
                v-model.number="sigHeight" 
                min="10" 
                :max="origSigHeight - cropTop"
                class="w-full mt-1"
              />
            </div>
          </div>

          <!-- Quick Position Buttons -->
          <div>
            <label class="label-mono mb-2 block">Quick Position:</label>
            <div class="grid grid-cols-3 gap-2">
              <button 
                @click="setQuickPosition('bottom-left')"
                class="btn-mono-secondary text-xs py-2"
              >Bottom Left</button>
              <button 
                @click="setQuickPosition('bottom-center')"
                class="btn-mono-secondary text-xs py-2"
              >Bottom Center</button>
              <button 
                @click="setQuickPosition('bottom-right')"
                class="btn-mono-secondary text-xs py-2"
              >Bottom Right</button>
            </div>
          </div>

          <!-- Manual Position (collapsible) -->
          <details class="border border-[var(--border-light)]">
            <summary class="p-3 cursor-pointer text-sm text-[var(--muted-foreground)] hover:bg-[var(--muted)]">
              Manual position (advanced)
            </summary>
            <div class="p-3 grid grid-cols-2 gap-4 border-t border-[var(--border-light)]">
              <div>
                <label class="label-mono">X Position</label>
                <input 
                  type="number" 
                  v-model.number="posX" 
                  min="0" 
                  :max="pdfInfo ? pdfInfo.width : 612"
                  class="input-mono w-full"
                />
              </div>
              <div>
                <label class="label-mono">Y Position</label>
                <input 
                  type="number" 
                  v-model.number="posY" 
                  min="0" 
                  :max="pdfInfo ? pdfInfo.height : 792"
                  class="input-mono w-full"
                />
              </div>
            </div>
          </details>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="alert-mono-error flex items-start space-x-3">
        <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 flex-shrink-0 mt-0.5" />
        <p class="text-sm">{{ error }}</p>
      </div>

      <!-- Success Message -->
      <div v-if="downloadUrl" class="alert-mono-success text-center">
        <Icon name="heroicons:check-circle" class="w-12 h-12 mx-auto mb-4" />
        <p class="font-serif font-bold text-lg mb-2">PDF Signed Successfully!</p>
        <a 
          :href="downloadUrl" 
          :download="`signed_${pdfFile?.name || 'document.pdf'}`"
          class="btn-mono-primary inline-flex"
        >
          <Icon name="heroicons:arrow-down-tray" class="w-4 h-4 mr-2" />
          Download Signed PDF
        </a>
      </div>

      <!-- Action Button -->
      <button 
        v-if="pdfFile && hasSignature && !downloadUrl"
        @click="signPdf"
        :disabled="processing"
        class="btn-mono-primary w-full py-4 text-lg"
      >
        <span v-if="processing" class="flex items-center justify-center">
          <div class="w-5 h-5 border-2 border-[var(--background)]/30 border-t-[var(--background)] animate-spin mr-3"></div>
          Signing PDF...
        </span>
        <span v-else class="flex items-center justify-center">
          <Icon name="heroicons:pencil-square" class="w-5 h-5 mr-3" />
          Sign PDF
        </span>
      </button>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  middleware: ['auth']
})

useHead({
  title: 'Sign PDF — ManTuls'
})

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

// Refs
const pdfInput = ref(null)
const sigInput = ref(null)
const signatureCanvas = ref(null)
const previewContainer = ref(null)
const previewImage = ref(null)
const signatureOverlay = ref(null)

// State
const isDragging = ref(false)
const pdfFile = ref(null)
const pdfInfo = ref(null)
const signatureMode = ref('draw')
const uploadedSignature = ref(null)
const uploadedSignaturePreview = ref(null)
const penColor = ref('#000000')

const selectedPage = ref(1)
const posX = ref(100)
const posY = ref(100)
const sigWidth = ref(200)
const sigHeight = ref(80) // Independent height for cropping

// Original signature dimensions (before crop)
const origSigWidth = ref(300)
const origSigHeight = ref(150)

// Crop offsets (how much we've cropped from each side)
const cropLeft = ref(0)
const cropTop = ref(0)

const processing = ref(false)
const error = ref(null)
const downloadUrl = ref(null)

// Preview state
const pagePreviewUrl = ref(null)
const loadingPreview = ref(false)
const signaturePreviewUrl = ref(null)
const previewScale = ref(1) // Ratio of preview size to actual PDF size

// Drag state
const isDraggingSignature = ref(false)
const dragStartX = ref(0)
const dragStartY = ref(0)
const overlayX = ref(50) // Position in preview pixels
const overlayY = ref(50)

// Drawing state
const isDrawing = ref(false)
const hasDrawnOnCanvas = ref(false) // Reactive trigger for canvas changes
let ctx = null

const hasSignature = computed(() => {
  if (signatureMode.value === 'upload') {
    return !!uploadedSignature.value
  }
  // Use reactive trigger for canvas content
  return hasDrawnOnCanvas.value
})

// Initialize canvas
onMounted(() => {
  if (signatureCanvas.value) {
    initCanvas()
  }
})

watch(signatureMode, () => {
  nextTick(() => {
    if (signatureMode.value === 'draw' && signatureCanvas.value) {
      initCanvas()
    }
  })
})

const initCanvas = () => {
  const canvas = signatureCanvas.value
  if (!canvas) return
  
  // Set actual canvas size
  const rect = canvas.getBoundingClientRect()
  canvas.width = rect.width * 2
  canvas.height = rect.height * 2
  
  ctx = canvas.getContext('2d')
  ctx.scale(2, 2)
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.lineWidth = 2
}

// PDF handling
const handlePdfSelect = async (event) => {
  const file = event.target.files[0]
  if (file && file.type === 'application/pdf') {
    await setPdfFile(file)
  }
}

const handlePdfDrop = async (event) => {
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file && file.type === 'application/pdf') {
    await setPdfFile(file)
  }
}

const setPdfFile = async (file) => {
  pdfFile.value = file
  downloadUrl.value = null
  error.value = null
  
  // Get PDF info
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await fetch(`${apiBase}/api/v1/tools/pdf-info`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      pdfInfo.value = await response.json()
      // Load preview after getting info
      await loadPagePreview()
    }
  } catch (e) {
    console.error('Failed to get PDF info:', e)
  }
}

const clearPdf = () => {
  pdfFile.value = null
  pdfInfo.value = null
  downloadUrl.value = null
  pagePreviewUrl.value = null
}

// PDF Preview
const loadPagePreview = async () => {
  if (!pdfFile.value) return
  
  loadingPreview.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', pdfFile.value)
    
    const response = await fetch(`${apiBase}/api/v1/tools/pdf-preview?page=${selectedPage.value}`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const blob = await response.blob()
      if (pagePreviewUrl.value) {
        URL.revokeObjectURL(pagePreviewUrl.value)
      }
      pagePreviewUrl.value = URL.createObjectURL(blob)
    }
  } catch (e) {
    console.error('Failed to load preview:', e)
  } finally {
    loadingPreview.value = false
  }
}

const onPreviewLoad = () => {
  if (!previewImage.value || !pdfInfo.value) return
  
  // Calculate scale ratio
  const displayWidth = previewImage.value.clientWidth
  previewScale.value = displayWidth / pdfInfo.value.width
  
  // Update signature preview if we have a signature
  updateSignaturePreview()
  
  // Set initial position
  updateOverlayFromPdfCoords()
}

// Signature preview for the overlay
const updateSignaturePreview = async () => {
  if (signatureMode.value === 'upload' && uploadedSignaturePreview.value) {
    signaturePreviewUrl.value = uploadedSignaturePreview.value
    // Set default original dimensions for uploaded image (larger for flexibility)
    origSigWidth.value = 300
    origSigHeight.value = 150
  } else if (signatureMode.value === 'draw' && signatureCanvas.value && hasDrawnOnCanvas.value) {
    const canvas = signatureCanvas.value
    signaturePreviewUrl.value = canvas.toDataURL('image/png')
    
    // Set original dimensions based on canvas aspect ratio (larger for flexibility)
    const aspectRatio = canvas.width / canvas.height
    origSigWidth.value = 300
    origSigHeight.value = Math.round(300 / aspectRatio)
  }
  
  // Reset crop and dimensions to original
  sigWidth.value = origSigWidth.value
  sigHeight.value = origSigHeight.value
  cropLeft.value = 0
  cropTop.value = 0
}

// Watch for signature changes
watch([hasDrawnOnCanvas, uploadedSignaturePreview, signatureMode], () => {
  updateSignaturePreview()
})

// Convert PDF coords to overlay position and vice versa
const updateOverlayFromPdfCoords = () => {
  if (!pdfInfo.value) return
  
  // PDF Y is from bottom, but display Y is from top
  const displayHeight = previewImage.value?.clientHeight || 400
  overlayX.value = posX.value * previewScale.value
  overlayY.value = displayHeight - (posY.value + sigHeight.value) * previewScale.value
}

const updatePdfCoordsFromOverlay = () => {
  if (!pdfInfo.value || !previewImage.value) return
  
  const displayHeight = previewImage.value.clientHeight
  posX.value = Math.round(overlayX.value / previewScale.value)
  posY.value = Math.round((displayHeight - overlayY.value - sigHeight.value * previewScale.value) / previewScale.value)
}

// Computed style for signature overlay
const signatureOverlayStyle = computed(() => {
  const width = sigWidth.value * previewScale.value
  const height = sigHeight.value * previewScale.value
  return {
    left: `${overlayX.value}px`,
    top: `${overlayY.value}px`,
    width: `${width}px`,
    height: `${height}px`
  }
})

// Computed style for signature image (positioned inside overlay for cropping)
const signatureImageStyle = computed(() => {
  const imgWidth = origSigWidth.value * previewScale.value
  const imgHeight = origSigHeight.value * previewScale.value
  const offsetX = -cropLeft.value * previewScale.value
  const offsetY = -cropTop.value * previewScale.value
  return {
    width: `${imgWidth}px`,
    height: `${imgHeight}px`,
    left: `${offsetX}px`,
    top: `${offsetY}px`
  }
})

// Drag handlers
const startDrag = (event) => {
  isDraggingSignature.value = true
  dragStartX.value = event.clientX - overlayX.value
  dragStartY.value = event.clientY - overlayY.value
  
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const startDragTouch = (event) => {
  const touch = event.touches[0]
  isDraggingSignature.value = true
  dragStartX.value = touch.clientX - overlayX.value
  dragStartY.value = touch.clientY - overlayY.value
  
  document.addEventListener('touchmove', onDragTouch)
  document.addEventListener('touchend', stopDrag)
}

const onDrag = (event) => {
  if (!isDraggingSignature.value || !previewContainer.value) return
  
  const containerRect = previewContainer.value.getBoundingClientRect()
  const sigDisplayWidth = sigWidth.value * previewScale.value
  const sigDisplayHeight = sigHeight.value * previewScale.value
  
  let newX = event.clientX - dragStartX.value
  let newY = event.clientY - dragStartY.value
  
  // Constrain within bounds
  newX = Math.max(0, Math.min(newX, containerRect.width - sigDisplayWidth))
  newY = Math.max(0, Math.min(newY, containerRect.height - sigDisplayHeight))
  
  overlayX.value = newX
  overlayY.value = newY
  
  updatePdfCoordsFromOverlay()
}

const onDragTouch = (event) => {
  const touch = event.touches[0]
  onDrag({ clientX: touch.clientX, clientY: touch.clientY })
}

const stopDrag = () => {
  isDraggingSignature.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('touchmove', onDragTouch)
  document.removeEventListener('touchend', stopDrag)
}

// Resize handlers
const isResizing = ref(false)
const resizeStartX = ref(0)
const resizeStartY = ref(0)
const resizeStartWidth = ref(0)
const resizeStartHeight = ref(0)
const resizeStartOverlayX = ref(0)
const resizeStartOverlayY = ref(0)
const resizeStartCropLeft = ref(0)
const resizeStartCropTop = ref(0)
const resizeDirection = ref('se') // nw, ne, sw, se, n, s, e, w

const startResize = (event, direction = 'se') => {
  isResizing.value = true
  resizeDirection.value = direction
  resizeStartX.value = event.clientX
  resizeStartY.value = event.clientY
  resizeStartWidth.value = sigWidth.value
  resizeStartHeight.value = sigHeight.value
  resizeStartOverlayX.value = overlayX.value
  resizeStartOverlayY.value = overlayY.value
  resizeStartCropLeft.value = cropLeft.value
  resizeStartCropTop.value = cropTop.value
  
  document.addEventListener('mousemove', onResize)
  document.addEventListener('mouseup', stopResize)
}

const startResizeTouch = (event, direction = 'se') => {
  const touch = event.touches[0]
  isResizing.value = true
  resizeDirection.value = direction
  resizeStartX.value = touch.clientX
  resizeStartY.value = touch.clientY
  resizeStartWidth.value = sigWidth.value
  resizeStartHeight.value = sigHeight.value
  resizeStartOverlayX.value = overlayX.value
  resizeStartOverlayY.value = overlayY.value
  resizeStartCropLeft.value = cropLeft.value
  resizeStartCropTop.value = cropTop.value
  
  document.addEventListener('touchmove', onResizeTouch)
  document.addEventListener('touchend', stopResize)
}

const onResize = (event) => {
  if (!isResizing.value) return
  
  const deltaX = event.clientX - resizeStartX.value
  const deltaY = event.clientY - resizeStartY.value
  const dir = resizeDirection.value
  
  // Convert screen delta to PDF points
  const deltaXPdf = deltaX / previewScale.value
  const deltaYPdf = deltaY / previewScale.value
  
  let newWidth = resizeStartWidth.value
  let newHeight = resizeStartHeight.value
  let newX = resizeStartOverlayX.value
  let newY = resizeStartOverlayY.value
  let newCropLeft = resizeStartCropLeft.value
  let newCropTop = resizeStartCropTop.value
  
  // Handle corner directions
  if (dir === 'se') {
    // Bottom-right: dragging right/down expands, left/up crops
    newWidth = resizeStartWidth.value + deltaXPdf
    newHeight = resizeStartHeight.value + deltaYPdf
  } else if (dir === 'sw') {
    // Bottom-left: dragging right crops from left, down expands height
    // deltaX positive = moving right = increase crop from left
    newCropLeft = resizeStartCropLeft.value + deltaXPdf
    newWidth = resizeStartWidth.value - deltaXPdf
    newHeight = resizeStartHeight.value + deltaYPdf
    newX = resizeStartOverlayX.value + deltaX
  } else if (dir === 'ne') {
    // Top-right: dragging down crops from top, right expands width
    // deltaY positive = moving down = increase crop from top
    newCropTop = resizeStartCropTop.value + deltaYPdf
    newWidth = resizeStartWidth.value + deltaXPdf
    newHeight = resizeStartHeight.value - deltaYPdf
    newY = resizeStartOverlayY.value + deltaY
  } else if (dir === 'nw') {
    // Top-left: dragging right/down crops from left/top
    newCropLeft = resizeStartCropLeft.value + deltaXPdf
    newCropTop = resizeStartCropTop.value + deltaYPdf
    newWidth = resizeStartWidth.value - deltaXPdf
    newHeight = resizeStartHeight.value - deltaYPdf
    newX = resizeStartOverlayX.value + deltaX
    newY = resizeStartOverlayY.value + deltaY
  }
  // Handle edge directions (single axis cropping)
  else if (dir === 'n') {
    // Top edge: dragging down crops from top, up expands
    newCropTop = resizeStartCropTop.value + deltaYPdf
    newHeight = resizeStartHeight.value - deltaYPdf
    newY = resizeStartOverlayY.value + deltaY
  } else if (dir === 's') {
    // Bottom edge: dragging down expands, up crops
    newHeight = resizeStartHeight.value + deltaYPdf
  } else if (dir === 'w') {
    // Left edge: dragging right crops from left, left expands
    newCropLeft = resizeStartCropLeft.value + deltaXPdf
    newWidth = resizeStartWidth.value - deltaXPdf
    newX = resizeStartOverlayX.value + deltaX
  } else if (dir === 'e') {
    // Right edge: dragging right expands, left crops
    newWidth = resizeStartWidth.value + deltaXPdf
  }
  
  // First, constrain crop offsets (can't be negative)
  newCropLeft = Math.max(0, newCropLeft)
  newCropTop = Math.max(0, newCropTop)
  
  // Calculate max allowed crop (can't crop more than the image allows)
  const maxCropLeft = origSigWidth.value - 20
  const maxCropTop = origSigHeight.value - 10
  newCropLeft = Math.min(maxCropLeft, newCropLeft)
  newCropTop = Math.min(maxCropTop, newCropTop)
  
  // Now constrain width and height based on remaining visible area after crop
  const maxWidth = origSigWidth.value - newCropLeft
  const maxHeight = origSigHeight.value - newCropTop
  newWidth = Math.max(20, Math.min(maxWidth, newWidth))
  newHeight = Math.max(10, Math.min(maxHeight, newHeight))

  
  // Update values
  sigWidth.value = Math.round(newWidth)
  sigHeight.value = Math.round(newHeight)
  cropLeft.value = Math.round(newCropLeft)
  cropTop.value = Math.round(newCropTop)
  
  // Update position for edges/corners that move the overlay
  if (dir === 'w' || dir === 'sw' || dir === 'nw') {
    overlayX.value = Math.max(0, newX)
  }
  if (dir === 'n' || dir === 'ne' || dir === 'nw') {
    overlayY.value = Math.max(0, newY)
  }
  
  updatePdfCoordsFromOverlay()
}

const onResizeTouch = (event) => {
  const touch = event.touches[0]
  onResize({ clientX: touch.clientX, clientY: touch.clientY })
}

const stopResize = () => {
  isResizing.value = false
  document.removeEventListener('mousemove', onResize)
  document.removeEventListener('mouseup', stopResize)
  document.removeEventListener('touchmove', onResizeTouch)
  document.removeEventListener('touchend', stopResize)
}

// Signature drawing
const getCanvasCoords = (event) => {
  const canvas = signatureCanvas.value
  const rect = canvas.getBoundingClientRect()
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top
  }
}

const startDrawing = (event) => {
  isDrawing.value = true
  const coords = getCanvasCoords(event)
  ctx.strokeStyle = penColor.value
  ctx.beginPath()
  ctx.moveTo(coords.x, coords.y)
}

const draw = (event) => {
  if (!isDrawing.value) return
  const coords = getCanvasCoords(event)
  ctx.lineTo(coords.x, coords.y)
  ctx.stroke()
}

const stopDrawing = () => {
  if (isDrawing.value) {
    hasDrawnOnCanvas.value = true // Mark that user has drawn something
    // Update signature preview immediately after each stroke
    updateSignaturePreview()
  }
  isDrawing.value = false
}

const startDrawingTouch = (event) => {
  const touch = event.touches[0]
  startDrawing({ clientX: touch.clientX, clientY: touch.clientY })
}

const drawTouch = (event) => {
  const touch = event.touches[0]
  draw({ clientX: touch.clientX, clientY: touch.clientY })
}

const clearSignature = () => {
  if (!signatureCanvas.value) return
  const canvas = signatureCanvas.value
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  hasDrawnOnCanvas.value = false // Reset the reactive trigger
}

// Upload signature
const handleSignatureUpload = (event) => {
  const file = event.target.files[0]
  if (file && file.type.startsWith('image/')) {
    uploadedSignature.value = file
    uploadedSignaturePreview.value = URL.createObjectURL(file)
  }
}

const clearUploadedSignature = () => {
  if (uploadedSignaturePreview.value) {
    URL.revokeObjectURL(uploadedSignaturePreview.value)
  }
  uploadedSignature.value = null
  uploadedSignaturePreview.value = null
}

// Quick position
const setQuickPosition = (position) => {
  if (!pdfInfo.value) return
  
  const margin = 50
  switch (position) {
    case 'bottom-left':
      posX.value = margin
      posY.value = margin
      break
    case 'bottom-center':
      posX.value = (pdfInfo.value.width - sigWidth.value) / 2
      posY.value = margin
      break
    case 'bottom-right':
      posX.value = pdfInfo.value.width - sigWidth.value - margin
      posY.value = margin
      break
  }
  
  // Update visual overlay to match
  updateOverlayFromPdfCoords()
}

// Sign PDF
const signPdf = async () => {
  if (!pdfFile.value || !hasSignature.value) return
  
  processing.value = true
  error.value = null
  downloadUrl.value = null
  
  try {
    const formData = new FormData()
    formData.append('file', pdfFile.value)
    formData.append('page', selectedPage.value)
    formData.append('x', posX.value)
    formData.append('y', posY.value)
    formData.append('width', sigWidth.value)
    formData.append('height', sigHeight.value)
    
    // Get signature as blob
    let signatureBlob
    if (signatureMode.value === 'upload') {
      signatureBlob = uploadedSignature.value
    } else {
      // Convert canvas to blob
      const canvas = signatureCanvas.value
      signatureBlob = await new Promise(resolve => {
        canvas.toBlob(resolve, 'image/png')
      })
    }
    
    formData.append('signature', signatureBlob, 'signature.png')
    
    const response = await fetch(`${apiBase}/api/v1/tools/sign-pdf`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Failed to sign PDF')
    }
    
    // Create blob with explicit PDF MIME type
    const arrayBuffer = await response.arrayBuffer()
    const blob = new Blob([arrayBuffer], { type: 'application/pdf' })
    downloadUrl.value = URL.createObjectURL(blob)
  } catch (err) {
    error.value = err.message
  } finally {
    processing.value = false
  }
}
</script>

<style scoped>
.input-mono {
  @apply px-3 py-2 border-2 border-[var(--foreground)] bg-[var(--background)] focus:outline-none focus:ring-2 focus:ring-[var(--foreground)];
}

.label-mono {
  @apply block text-xs uppercase tracking-widest text-[var(--muted-foreground)] mb-1;
}

.btn-mono-secondary {
  @apply px-4 py-2 border-2 border-[var(--foreground)] hover:bg-[var(--muted)] transition-colors;
}
</style>
