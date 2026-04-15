<script setup lang="ts">
/**
 * ExcalidrawWrapper.vue
 *
 * Mounts the React-based Excalidraw library inside a Vue component.
 * Strategy: dynamically import React + Excalidraw on the client only,
 * then call ReactDOM.createRoot() on a div ref.
 *
 * Props
 *   initialElements  – Excalidraw element array (from DB / WS sync)
 *   initialAppState  – Excalidraw appState object
 *   readonly         – disable editing (viewer role)
 *
 * Emits
 *   change   – { elements, appState }  debounced 500 ms
 *   cursor   – { x, y }               throttled 100 ms
 *
 * Exposed
 *   updateScene(elements, appState)  – called by parent on WS update
 *   exportBlob()                     – returns PNG Blob for thumbnail
 */

import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  initialElements?: any[]
  initialAppState?: Record<string, any>
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'change', payload: { elements: any[]; appState: Record<string, any> }): void
  (e: 'cursor', payload: { x: number; y: number }): void
}>()

// ── Refs ────────────────────────────────────────────────────────────────────
const containerRef = ref<HTMLDivElement | null>(null)
const isLoading = ref(true)
const loadError = ref('')

// Stored across re-renders via module-scope closures
let _root: any = null
let _excalidrawAPI: any = null
let _React: any = null
let _Excalidraw: any = null
let _exportToBlob: any = null

// ── Pending update queue ────────────────────────────────────────────────────
// Holds the latest elements/appState that arrived before _excalidrawAPI was
// ready. Applied automatically the moment the API handle becomes available.
let _pendingUpdate: { elements: any[]; appState: any } | null = null

// ── Debounce / throttle helpers ─────────────────────────────────────────────
function debounce<T extends (...args: any[]) => void>(fn: T, ms: number): T {
  let timer: ReturnType<typeof setTimeout>
  return ((...args: any[]) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), ms)
  }) as T
}

function throttle<T extends (...args: any[]) => void>(fn: T, ms: number): T {
  let last = 0
  return ((...args: any[]) => {
    const now = Date.now()
    if (now - last >= ms) {
      last = now
      fn(...args)
    }
  }) as T
}

// ── appState sanitiser ──────────────────────────────────────────────────────
// Excalidraw requires appState.collaborators to be a Map<string, Collaborator>.
// JSON serialisation turns Map → plain object; this restores the correct type.
function sanitizeAppState(raw: any): any {
  if (!raw) return { collaborators: new Map() }
  const { collaborators, ...rest } = raw
  return {
    ...rest,
    collaborators:
      collaborators instanceof Map
        ? collaborators
        : new Map(Object.entries(collaborators ?? {})),
  }
}

// ── Emitters (debounced / throttled) ────────────────────────────────────────
const emitChange = debounce((elements: any[], appState: any) => {
  // Strip collaborators (Map) before emitting — not needed by parent and
  // cannot be JSON-serialised correctly.
  const { collaborators: _col, ...serializableState } = appState ?? {}
  emit('change', { elements, appState: serializableState })
}, 500)

const emitCursor = throttle((x: number, y: number) => {
  emit('cursor', { x, y })
}, 100)

// ── Mount React ──────────────────────────────────────────────────────────────
async function mountExcalidraw() {
  if (!containerRef.value) return

  try {
    _React = (await import('react')).default
    const { createRoot } = await import('react-dom/client')
    const excalidrawModule = await import('@excalidraw/excalidraw')
    _Excalidraw = excalidrawModule.Excalidraw
    _exportToBlob = excalidrawModule.exportToBlob

    _root = createRoot(containerRef.value)
    renderExcalidraw()
    isLoading.value = false
  } catch (err: any) {
    loadError.value = err?.message || 'Failed to load Excalidraw'
    isLoading.value = false
  }
}

function renderExcalidraw(overrideElements?: any[], overrideAppState?: any) {
  if (!_root || !_React || !_Excalidraw) return

  const elements = overrideElements ?? props.initialElements ?? []
  const appState = overrideAppState ?? props.initialAppState ?? {}

  _root.render(
    _React.createElement(_Excalidraw, {
      // API handle — defer pending update to next tick so Excalidraw finishes
      // mounting before we call setState via updateScene (avoids React warning).
      excalidrawAPI: (api: any) => {
        _excalidrawAPI = api
        if (_pendingUpdate) {
          const pending = _pendingUpdate
          _pendingUpdate = null
          setTimeout(() => {
            if (_excalidrawAPI === api) {
              api.updateScene({
                elements: pending.elements,
                ...(pending.appState
                  ? { appState: sanitizeAppState(pending.appState) }
                  : {}),
              })
            }
          }, 0)
        }
      },

      // Initial data (only read by Excalidraw on first mount)
      initialData: {
        elements,
        appState: {
          ...sanitizeAppState(appState),
          viewBackgroundColor: '#ffffff',
        },
      },

      viewModeEnabled: props.readonly ?? false,

      onChange: (els: any[], state: any) => {
        emitChange(els, state)
      },

      onPointerUpdate: ({ pointer }: { pointer: { x: number; y: number } }) => {
        emitCursor(pointer.x, pointer.y)
      },

      theme: 'light',

      UIOptions: {
        canvasActions: {
          saveToActiveFile: false,
          loadScene: false,
          export: { saveFileToDisk: true },
        },
      },
    })
  )
}

// ── Exposed API for parent component ─────────────────────────────────────────
function updateScene(elements: any[], appState?: Record<string, any>) {
  if (_excalidrawAPI) {
    // API ready — apply immediately, always sanitize collaborators → Map
    _excalidrawAPI.updateScene({
      elements,
      ...(appState ? { appState: sanitizeAppState(appState) } : {}),
    })
  } else {
    // API not ready yet — queue it; applied in the excalidrawAPI callback above
    _pendingUpdate = { elements, appState: appState ?? {} }
  }
}

async function exportBlob(): Promise<Blob | null> {
  if (!_excalidrawAPI || !_exportToBlob) return null
  try {
    return await _exportToBlob({
      elements: _excalidrawAPI.getSceneElements(),
      appState: _excalidrawAPI.getAppState(),
      mimeType: 'image/png',
      quality: 0.5,
    })
  } catch {
    return null
  }
}

function getElements(): any[] {
  return _excalidrawAPI?.getSceneElements() ?? []
}

defineExpose({ updateScene, exportBlob, getElements })

// ── Watch: apply when parent sets initialElements after canvas is mounted ─────
// Uses updateScene (with pending queue) instead of renderExcalidraw, because
// Excalidraw's initialData is only read once on first mount — re-rendering
// with new initialData has no effect on an already-mounted canvas.
watch(
  () => props.initialElements,
  (newEls) => {
    if (newEls?.length) updateScene(newEls, props.initialAppState)
  }
)

// ── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(mountExcalidraw)

onUnmounted(() => {
  if (_root) {
    _root.unmount()
    _root = null
    _excalidrawAPI = null
  }
})
</script>

<template>
  <div class="excalidraw-host">
    <!-- Loading splash -->
    <div v-if="isLoading" class="excalidraw-loading">
      <div class="excalidraw-loading__ring" />
      <span>Loading canvas…</span>
    </div>

    <!-- Error -->
    <div v-else-if="loadError" class="excalidraw-error">
      <span>{{ loadError }}</span>
    </div>

    <!-- React mount point -->
    <div ref="containerRef" class="excalidraw-mount" />
  </div>
</template>

<style scoped>
.excalidraw-host {
  position: relative;
  width: 100%;
  height: 100%;
}

.excalidraw-mount {
  width: 100%;
  height: 100%;
}

/* Excalidraw needs its own z-stacking context */
:deep(.excalidraw) {
  width: 100% !important;
  height: 100% !important;
}

.excalidraw-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #525252;
  background: #fff;
  z-index: 10;
}

.excalidraw-loading__ring {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e5e5;
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.excalidraw-error {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #e03131;
  background: #fff;
}
</style>
