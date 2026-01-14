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
        SCANNER TO PDF
      </h1>
      <p class="text-[var(--muted-foreground)] mt-2 text-lg">
        Capture documents with your camera and convert to PDF
      </p>
    </div>

    <!-- Main Content -->
    <div class="border-2 border-[var(--foreground)] bg-[var(--background)]">
      <div class="p-6 md:p-8">
        
        <!-- Camera Permission Error -->
        <div v-if="cameraError" class="alert-mono-error mb-6">
          <div class="flex items-start space-x-3">
            <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p class="font-medium">Camera access denied</p>
              <p class="text-sm mt-1">{{ cameraError }}</p>
              <button 
                @click="startCamera" 
                class="text-sm underline mt-2 hover:no-underline"
              >
                Try again
              </button>
            </div>
          </div>
        </div>

        <!-- Camera View -->
        <div v-if="!cameraError && !showFileUpload" class="space-y-6">
          
          <!-- Video Preview -->
          <div 
            class="relative border-2 border-[var(--foreground)] bg-black aspect-[4/3] overflow-hidden"
          >
            <video 
              ref="videoElement" 
              autoplay 
              playsinline 
              class="w-full h-full object-cover"
              :class="{ 'hidden': !isCameraActive }"
            ></video>
            
            <!-- Loading State -->
            <div 
              v-if="!isCameraActive && !cameraError" 
              class="absolute inset-0 flex items-center justify-center bg-[var(--muted)]"
            >
              <div class="text-center">
                <div class="w-8 h-8 border-2 border-[var(--foreground)]/30 border-t-[var(--foreground)] animate-spin mx-auto mb-4"></div>
                <p class="text-sm text-[var(--muted-foreground)]">Starting camera...</p>
              </div>
            </div>

            <!-- Camera Switch (mobile) -->
            <button 
              v-if="isCameraActive && hasMultipleCameras"
              @click="switchCamera"
              class="absolute top-3 right-3 w-10 h-10 bg-[var(--background)] border-2 border-[var(--foreground)] flex items-center justify-center"
            >
              <Icon name="heroicons:arrow-path" class="w-5 h-5" />
            </button>
          </div>

          <!-- Capture Button -->
          <button 
            @click="captureImage"
            :disabled="!isCameraActive"
            class="btn-mono-primary w-full py-4 text-lg flex items-center justify-center disabled:opacity-50"
          >
            <Icon name="heroicons:camera" class="w-6 h-6 mr-3" />
            Capture Page
          </button>

          <!-- Or Use File Upload -->
          <div class="text-center">
            <button 
              @click="showFileUpload = true; stopCamera()"
              class="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] underline"
            >
              Or upload images from device
            </button>
          </div>
        </div>

        <!-- File Upload Mode -->
        <div v-if="showFileUpload" class="space-y-6">
          <div 
            class="border-2 border-dashed border-[var(--foreground)] p-12 text-center cursor-pointer transition-colors duration-100"
            :class="{ 
              'bg-[var(--foreground)] text-[var(--background)]': isDragging,
              'hover:bg-[var(--muted)]': !isDragging
            }"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="handleFileDrop"
            @click="$refs.fileInput.click()"
          >
            <div 
              class="inline-flex items-center justify-center w-16 h-16 border-2 mb-6 transition-colors duration-100"
              :class="isDragging ? 'border-[var(--background)]' : 'border-[var(--foreground)]'"
            >
              <Icon 
                name="heroicons:photo" 
                class="w-8 h-8"
                :class="isDragging ? 'text-[var(--background)]' : 'text-[var(--muted-foreground)]'"
              />
            </div>
            
            <p class="font-serif text-lg font-medium mb-1">
              Drop images here or click to browse
            </p>
            <p class="text-sm" :class="isDragging ? 'text-[var(--background)]/70' : 'text-[var(--muted-foreground)]'">
              JPEG, PNG, WEBP supported
            </p>
          </div>

          <input 
            ref="fileInput" 
            type="file" 
            class="hidden" 
            accept="image/jpeg,image/png,image/webp"
            multiple
            @change="handleFileSelect"
          />

          <!-- Back to Camera -->
          <div class="text-center">
            <button 
              @click="showFileUpload = false; startCamera()"
              class="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] underline"
            >
              ← Back to camera
            </button>
          </div>
        </div>

        <!-- Captured Pages Preview -->
        <div v-if="capturedImages.length > 0" class="mt-8 pt-8 border-t-2 border-[var(--foreground)]">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-serif text-lg font-bold">
              Captured Pages ({{ capturedImages.length }})
            </h3>
            <button 
              @click="capturedImages = []"
              class="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
            >
              Clear all
            </button>
          </div>

          <!-- Thumbnails Grid -->
          <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
            <div 
              v-for="(img, index) in capturedImages" 
              :key="index"
              class="relative group aspect-[3/4] border-2 border-[var(--foreground)] overflow-hidden"
            >
              <img 
                :src="img.preview" 
                :alt="`Page ${index + 1}`"
                class="w-full h-full object-cover"
              />
              
              <!-- Page Number -->
              <div class="absolute top-1 left-1 w-6 h-6 bg-[var(--foreground)] text-[var(--background)] text-xs font-bold flex items-center justify-center">
                {{ index + 1 }}
              </div>

              <!-- Delete Button -->
              <button 
                @click="removeImage(index)"
                class="absolute top-1 right-1 w-6 h-6 bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Icon name="heroicons:x-mark" class="w-4 h-4" />
              </button>
            </div>

            <!-- Add More Button -->
            <button 
              @click="showFileUpload ? $refs.fileInput.click() : null"
              v-if="!showFileUpload"
              class="aspect-[3/4] border-2 border-dashed border-[var(--foreground)] flex flex-col items-center justify-center text-[var(--muted-foreground)] hover:bg-[var(--muted)] transition-colors"
            >
              <Icon name="heroicons:plus" class="w-6 h-6 mb-1" />
              <span class="text-xs">Add</span>
            </button>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="alert-mono-error mt-6 flex items-start space-x-3">
          <Icon name="heroicons:exclamation-triangle" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p class="text-sm">{{ error }}</p>
        </div>

        <!-- Success Message -->
        <div v-if="downloadUrl" class="alert-mono-success mt-6 text-center">
          <Icon name="heroicons:check-circle" class="w-12 h-12 mx-auto mb-4" />
          <p class="font-serif font-bold text-lg mb-2">PDF Created Successfully!</p>
          <p class="text-sm text-[var(--muted-foreground)] mb-4">
            {{ capturedImages.length }} page(s) combined into PDF
          </p>
          <a 
            :href="downloadUrl" 
            download="scanned_document.pdf"
            class="btn-mono-primary inline-flex"
          >
            <Icon name="heroicons:arrow-down-tray" class="w-4 h-4 mr-2" />
            Download PDF
          </a>
        </div>

        <!-- Hidden Canvas for Capturing -->
        <canvas ref="canvasElement" class="hidden"></canvas>
      </div>

      <!-- Action Button -->
      <div 
        v-if="capturedImages.length > 0 && !downloadUrl" 
        class="p-6 border-t-2 border-[var(--foreground)] bg-[var(--muted)]"
      >
        <button 
          @click="generatePDF" 
          :disabled="processing"
          class="btn-mono-primary w-full"
        >
          <span v-if="processing" class="flex items-center justify-center">
            <div class="w-4 h-4 border-2 border-[var(--background)]/30 border-t-[var(--background)] animate-spin mr-2"></div>
            Generating PDF...
          </span>
          <span v-else class="flex items-center justify-center">
            <Icon name="heroicons:document" class="w-4 h-4 mr-2" />
            Generate PDF ({{ capturedImages.length }} pages)
          </span>
        </button>
      </div>
    </div>

    <!-- Mobile Tip -->
    <div class="mt-6 p-4 border border-[var(--border-light)] text-sm text-[var(--muted-foreground)]">
      <div class="flex items-start space-x-3">
        <Icon name="heroicons:device-phone-mobile" class="w-5 h-5 flex-shrink-0 mt-0.5" />
        <p>
          <strong>Tip:</strong> This tool works best on mobile devices. Use your phone's camera to scan documents quickly.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  middleware: ['auth']
})

useHead({
  title: 'Scanner to PDF — ManTuls'
})

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

// Refs
const videoElement = ref(null)
const canvasElement = ref(null)
const fileInput = ref(null)

// State
const isCameraActive = ref(false)
const cameraError = ref(null)
const hasMultipleCameras = ref(false)
const currentFacingMode = ref('environment') // 'environment' = back camera
const showFileUpload = ref(false)
const isDragging = ref(false)
const capturedImages = ref([])
const processing = ref(false)
const error = ref(null)
const downloadUrl = ref(null)

let mediaStream = null

// Start camera on mount
onMounted(async () => {
  // Check if we're on mobile - prefer camera, otherwise show upload
  const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  
  if (isMobile) {
    await startCamera()
  } else {
    // On desktop, try camera first but don't show error if it fails
    try {
      await startCamera()
    } catch {
      showFileUpload.value = true
    }
  }
  
  // Check for multiple cameras
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    const videoDevices = devices.filter(d => d.kind === 'videoinput')
    hasMultipleCameras.value = videoDevices.length > 1
  } catch {
    // Ignore
  }
})

// Clean up on unmount
onUnmounted(() => {
  stopCamera()
})

const startCamera = async () => {
  cameraError.value = null
  
  try {
    const constraints = {
      video: {
        facingMode: { ideal: currentFacingMode.value },
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: false
    }
    
    mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
    
    if (videoElement.value) {
      videoElement.value.srcObject = mediaStream
      isCameraActive.value = true
    }
  } catch (err) {
    console.error('Camera error:', err)
    if (err.name === 'NotAllowedError') {
      cameraError.value = 'Camera permission was denied. Please allow camera access and try again.'
    } else if (err.name === 'NotFoundError') {
      cameraError.value = 'No camera found. Use file upload instead.'
      showFileUpload.value = true
    } else {
      cameraError.value = `Failed to start camera: ${err.message}`
    }
    isCameraActive.value = false
  }
}

const stopCamera = () => {
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  isCameraActive.value = false
}

const switchCamera = async () => {
  currentFacingMode.value = currentFacingMode.value === 'environment' ? 'user' : 'environment'
  stopCamera()
  await startCamera()
}

const captureImage = () => {
  if (!videoElement.value || !canvasElement.value) return
  
  const video = videoElement.value
  const canvas = canvasElement.value
  
  // Set canvas size to match video
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  
  // Draw video frame to canvas
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0)
  
  // Get image data
  canvas.toBlob((blob) => {
    if (blob) {
      capturedImages.value.push({
        blob,
        preview: URL.createObjectURL(blob)
      })
      
      // Reset download URL when new image added
      downloadUrl.value = null
      error.value = null
    }
  }, 'image/jpeg', 0.9)
}

const handleFileSelect = (event) => {
  const files = event.target.files
  addFilesToCapture(files)
}

const handleFileDrop = (event) => {
  isDragging.value = false
  const files = event.dataTransfer.files
  addFilesToCapture(files)
}

const addFilesToCapture = (files) => {
  for (const file of files) {
    if (file.type.startsWith('image/')) {
      capturedImages.value.push({
        blob: file,
        preview: URL.createObjectURL(file)
      })
    }
  }
  
  // Reset
  downloadUrl.value = null
  error.value = null
}

const removeImage = (index) => {
  const img = capturedImages.value[index]
  if (img.preview) {
    URL.revokeObjectURL(img.preview)
  }
  capturedImages.value.splice(index, 1)
  
  // Reset download URL
  downloadUrl.value = null
}

const generatePDF = async () => {
  if (capturedImages.value.length === 0) return
  
  processing.value = true
  error.value = null
  downloadUrl.value = null
  
  try {
    const formData = new FormData()
    
    capturedImages.value.forEach((img, index) => {
      formData.append('files', img.blob, `page_${index + 1}.jpg`)
    })
    
    const response = await fetch(`${apiBase}/api/v1/tools/images-to-pdf`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      throw new Error(errData.detail || 'Failed to generate PDF')
    }
    
    const blob = await response.blob()
    downloadUrl.value = URL.createObjectURL(blob)
  } catch (err) {
    error.value = err.message
  } finally {
    processing.value = false
  }
}
</script>
