<template>
  <div class="flex flex-col items-center justify-center py-6 space-y-3">
    <!-- Spinning ring with progress -->
    <div class="relative w-16 h-16">
      <!-- Background ring -->
      <div class="absolute inset-0 border-4 border-[var(--muted)] rounded-full"></div>
      <!-- Spinning foreground ring -->
      <div 
        class="absolute inset-0 border-4 border-[var(--foreground)] rounded-full animate-spin"
        style="border-top-color: transparent; border-right-color: transparent; border-bottom-color: transparent;"
      ></div>
      <!-- Center icon (optional) -->
      <div class="absolute inset-0 flex items-center justify-center">
        <Icon v-if="icon" :name="icon" class="w-6 h-6 text-[var(--muted-foreground)]" />
      </div>
    </div>
    
    <!-- Status text -->
    <p class="font-serif font-medium text-lg">{{ statusText }}</p>
    
    <!-- Time estimate -->
    <div class="text-center">
      <p class="text-sm text-[var(--muted-foreground)]">
        Estimasi waktu: <span class="font-mono font-medium text-[var(--foreground)]">{{ formattedTimeRemaining }}</span>
      </p>
      <p v-if="elapsedSeconds > 0" class="text-xs text-[var(--muted-foreground)] mt-1">
        Sudah berjalan: {{ formattedElapsed }}
      </p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  statusText: {
    type: String,
    default: 'Processing...'
  },
  estimatedSeconds: {
    type: Number,
    default: 5
  },
  icon: {
    type: String,
    default: null
  },
  active: {
    type: Boolean,
    default: true
  }
})

const startTime = ref(Date.now())
const elapsedSeconds = ref(0)
let intervalId = null

// Update elapsed time every 500ms
onMounted(() => {
  startTime.value = Date.now()
  elapsedSeconds.value = 0
  
  intervalId = setInterval(() => {
    elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
  }, 500)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})

// Reset timer when active changes
watch(() => props.active, (newVal) => {
  if (newVal) {
    startTime.value = Date.now()
    elapsedSeconds.value = 0
  }
})

const remainingSeconds = computed(() => {
  const remaining = props.estimatedSeconds - elapsedSeconds.value
  return Math.max(0, remaining)
})

const formattedTimeRemaining = computed(() => {
  const seconds = remainingSeconds.value
  if (seconds <= 0) {
    return 'hampir selesai...'
  }
  if (seconds < 60) {
    return `~${seconds} detik`
  }
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `~${minutes}m ${secs}s`
})

const formattedElapsed = computed(() => {
  const seconds = elapsedSeconds.value
  if (seconds < 60) {
    return `${seconds}s`
  }
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}m ${secs}s`
})
</script>
