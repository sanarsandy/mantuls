<script setup lang="ts">
import type { WsUser } from '~/composables/useWhiteboardWS'

definePageMeta({
  layout: 'whiteboard',
  middleware: 'auth',
})

const route   = useRoute()
const config  = useRuntimeConfig()
const apiBase = config.public.apiBase
const roomId  = route.params.room_id as string

// ── Auth ──────────────────────────────────────────────────────────────────
const tokenCookie = useCookie('ocr_token')
const userCookie  = useCookie('ocr_user')
const token = tokenCookie.value ?? ''

const authHeader = computed(() => ({
  Authorization: `Bearer ${token}`,
  'Content-Type': 'application/json',
}))

const me = computed(() => {
  try { return JSON.parse(userCookie.value as string) } catch { return null }
})

// ── Room state ─────────────────────────────────────────────────────────────
const room        = ref<any>(null)
const loadError   = ref('')
const isEditor    = ref(true)

// ── Canvas state ──────────────────────────────────────────────────────────
const initialElements = ref<any[]>([])
const initialAppState = ref<Record<string, any>>({})

// ── Collaboration state ───────────────────────────────────────────────────
const onlineUsers  = ref<WsUser[]>([])
const cursors      = ref<Map<string, { x: number; y: number; color: string }>>(new Map())

// ── UI panels ─────────────────────────────────────────────────────────────
const showHistory  = ref(false)
const showMembers  = ref(false)
const snapshots    = ref<any[]>([])
const loadingSnaps = ref(false)
const isSaving     = ref(false)
const saveMsg      = ref('')

// ── Excalidraw ref ────────────────────────────────────────────────────────
const canvasRef = ref<InstanceType<typeof import('~/components/whiteboard/ExcalidrawWrapper.vue').default> | null>(null)

// ── Auto-save interval (every 3 min) ─────────────────────────────────────
let autoSaveInterval: ReturnType<typeof setInterval> | null = null

// ── WS composable (set up after room loaded) ──────────────────────────────
let ws: ReturnType<typeof useWhiteboardWS> | null = null

// ── Fetch room info + initial data ────────────────────────────────────────
async function loadRoom() {
  try {
    const res = await fetch(`${apiBase}/api/v1/whiteboard/rooms/${roomId}`, {
      headers: authHeader.value,
    })
    if (!res.ok) {
      loadError.value = res.status === 403 ? 'Access denied' : 'Room not found'
      return
    }
    const data = await res.json()
    room.value          = data
    initialElements.value = data.elements  ?? []
    initialAppState.value = data.app_state ?? {}
    onlineUsers.value     = data.online_users ?? []
    isEditor.value        = data.is_owner ||
      (data.members ?? []).some((m: any) => m.email === me.value?.email && m.role === 'editor') ||
      data.is_owner
  } catch (e: any) {
    loadError.value = e?.message || 'Failed to load room'
  }
}

// ── WS setup ──────────────────────────────────────────────────────────────
function setupWS() {
  ws = useWhiteboardWS(roomId, token, {
    onSync(elements, appState, users, editorFlag) {
      // Update canvas if the live state is non-empty
      if (elements.length > 0) {
        canvasRef.value?.updateScene(elements, appState)
      }
      onlineUsers.value = users
      isEditor.value    = editorFlag
    },
    onUpdate(elements, appState) {
      canvasRef.value?.updateScene(elements, appState)
    },
    onCursor(email, color, x, y) {
      if (email === me.value?.email) return
      cursors.value = new Map(cursors.value).set(email, { x, y, color })
    },
    onPresence(action, user, users) {
      onlineUsers.value = users
      if (action === 'leave') {
        const c = new Map(cursors.value)
        c.delete(user.email)
        cursors.value = c
      }
    },
    onRestore(elements, appState, label) {
      canvasRef.value?.updateScene(elements, appState)
      saveMsg.value = `Restored: "${label}"`
      setTimeout(() => { saveMsg.value = '' }, 3000)
    },
    onError(msg) {
      console.error('WS error:', msg)
    },
  })
}

// ── Canvas event handlers ─────────────────────────────────────────────────
function onCanvasChange({ elements, appState }: { elements: any[]; appState: any }) {
  if (!isEditor.value) return
  ws?.sendUpdate(elements, appState)
}

function onCanvasCursor({ x, y }: { x: number; y: number }) {
  if (!isEditor.value) return
  ws?.sendCursor(x, y)
}

// ── Manual save (with thumbnail) ──────────────────────────────────────────
async function saveSnapshot(label = 'Manual save') {
  if (!canvasRef.value || isSaving.value) return
  isSaving.value = true
  saveMsg.value  = 'Saving…'
  try {
    // Get thumbnail from Excalidraw
    let thumbnail: string | null = null
    const blob = await canvasRef.value.exportBlob()
    if (blob) {
      const reader = new FileReader()
      thumbnail = await new Promise<string>(resolve => {
        reader.onload = () => resolve(reader.result as string)
        reader.readAsDataURL(blob)
      })
    }

    // Get current scene
    const elements = (canvasRef.value as any)._excalidrawAPI?.getSceneElements?.() ?? []

    const res = await fetch(`${apiBase}/api/v1/whiteboard/rooms/${roomId}/save`, {
      method: 'POST',
      headers: authHeader.value,
      body: JSON.stringify({ elements, app_state: {}, thumbnail, label }),
    })
    if (!res.ok) throw new Error(await res.text())
    saveMsg.value = 'Saved!'
    if (showHistory.value) await loadHistory()
  } catch (e: any) {
    saveMsg.value = 'Save failed'
  } finally {
    isSaving.value = false
    setTimeout(() => { saveMsg.value = '' }, 3000)
  }
}

// ── History panel ─────────────────────────────────────────────────────────
async function loadHistory() {
  loadingSnaps.value = true
  try {
    const res = await fetch(`${apiBase}/api/v1/whiteboard/rooms/${roomId}/history`, {
      headers: authHeader.value,
    })
    if (res.ok) snapshots.value = await res.json()
  } finally {
    loadingSnaps.value = false
  }
}

async function restoreSnapshot(snap: any) {
  if (!confirm(`Restore "${snap.label}" (${fmtDate(snap.created_at)})? Current canvas will be overwritten.`)) return
  try {
    const res = await fetch(`${apiBase}/api/v1/whiteboard/rooms/${roomId}/restore/${snap.id}`, {
      method: 'POST',
      headers: authHeader.value,
    })
    if (!res.ok) throw new Error(await res.text())
    showHistory.value = false
  } catch (e: any) {
    alert(e?.message || 'Restore failed')
  }
}

async function deleteSnapshot(snap: any) {
  if (!confirm(`Delete snapshot "${snap.label}"?`)) return
  try {
    await fetch(`${apiBase}/api/v1/whiteboard/rooms/${roomId}/history/${snap.id}`, {
      method: 'DELETE',
      headers: authHeader.value,
    })
    snapshots.value = snapshots.value.filter(s => s.id !== snap.id)
  } catch { /* ignore */ }
}

function toggleHistory() {
  showHistory.value = !showHistory.value
  showMembers.value = false
  if (showHistory.value) loadHistory()
}

function toggleMembers() {
  showMembers.value = !showMembers.value
  showHistory.value = false
}

function copyLink() {
  navigator.clipboard.writeText(window.location.href)
    .then(() => { saveMsg.value = 'Link copied!'; setTimeout(() => { saveMsg.value = '' }, 2000) })
}

// ── Formatting ────────────────────────────────────────────────────────────
function fmtDate(iso: string) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('id-ID', { dateStyle: 'medium', timeStyle: 'short' })
}

// ── Lifecycle ─────────────────────────────────────────────────────────────
onMounted(async () => {
  await loadRoom()
  if (!loadError.value) {
    setupWS()
    // Auto-save every 3 minutes
    autoSaveInterval = setInterval(() => {
      // Send actual current elements so backend has real data to snapshot.
      // Backend also cross-checks with its own in-memory state as fallback.
      const elements = canvasRef.value?.getElements() ?? []
      ws?.sendAutosave(elements, {})
    }, 3 * 60 * 1000)
  }
})

onUnmounted(() => {
  if (autoSaveInterval) clearInterval(autoSaveInterval)
})
</script>

<template>
  <div class="wb-page">

    <!-- ── Error screen ─────────────────────────────────────────────────── -->
    <div v-if="loadError" class="wb-error">
      <div class="wb-error__box">
        <Icon name="heroicons:exclamation-triangle" class="w-10 h-10 text-red-500 mb-3" />
        <p class="font-serif text-xl font-bold">{{ loadError }}</p>
        <NuxtLink to="/tools/whiteboard" class="mt-4 px-4 py-2 border-2 border-current font-mono text-sm hover:bg-black hover:text-white transition-colors">
          ← Back to Rooms
        </NuxtLink>
      </div>
    </div>

    <template v-else>
      <!-- ── Top bar ──────────────────────────────────────────────────── -->
      <div class="wb-topbar">
        <!-- Left: back + room name -->
        <div class="wb-topbar__left">
          <NuxtLink
            to="/tools/whiteboard"
            class="wb-btn"
            title="Back to rooms"
          ><Icon name="heroicons:arrow-left" class="w-4 h-4" /></NuxtLink>

          <span class="wb-room-name">{{ room?.name ?? '…' }}</span>

          <span
            v-if="!isEditor"
            class="wb-badge"
          >VIEW ONLY</span>

          <!-- WS status -->
          <span class="wb-dot" :class="ws?.isConnected.value ? 'wb-dot--on' : 'wb-dot--off'" />
          <span class="wb-status-text">
            <template v-if="ws?.isReconnecting.value">reconnecting…</template>
            <template v-else-if="ws?.isConnected.value">live</template>
            <template v-else>offline</template>
          </span>
        </div>

        <!-- Center: online users -->
        <div class="wb-topbar__center">
          <div
            v-for="user in onlineUsers"
            :key="user.email"
            class="wb-avatar"
            :style="{ background: user.color }"
            :title="user.name || user.email"
          >{{ (user.name || user.email).charAt(0).toUpperCase() }}</div>
        </div>

        <!-- Right: actions -->
        <div class="wb-topbar__right">
          <span v-if="saveMsg" class="wb-save-msg">{{ saveMsg }}</span>

          <button
            v-if="isEditor"
            class="wb-btn"
            title="Save snapshot"
            :disabled="isSaving"
            @click="saveSnapshot('Manual save')"
          ><Icon name="heroicons:cloud-arrow-up" class="w-4 h-4" /></button>

          <button
            class="wb-btn"
            :class="{ 'wb-btn--active': showHistory }"
            title="History"
            @click="toggleHistory"
          ><Icon name="heroicons:clock" class="w-4 h-4" /></button>

          <button
            v-if="room?.is_owner"
            class="wb-btn"
            :class="{ 'wb-btn--active': showMembers }"
            title="Members"
            @click="toggleMembers"
          ><Icon name="heroicons:users" class="w-4 h-4" /></button>

          <button class="wb-btn" title="Copy link" @click="copyLink">
            <Icon name="heroicons:link" class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- ── Canvas area ───────────────────────────────────────────────── -->
      <div class="wb-canvas-area">
        <!-- Excalidraw (client-only to avoid SSR issues) -->
        <ClientOnly>
          <WhiteboardExcalidrawWrapper
            ref="canvasRef"
            :initial-elements="initialElements"
            :initial-app-state="initialAppState"
            :readonly="!isEditor"
            @change="onCanvasChange"
            @cursor="onCanvasCursor"
          />
          <template #fallback>
            <div class="wb-canvas-loading">
              <div class="wb-spinner" />
              <span>Loading canvas…</span>
            </div>
          </template>
        </ClientOnly>

        <!-- Remote cursor overlays -->
        <div class="wb-cursors" aria-hidden="true">
          <div
            v-for="[email, pos] in cursors"
            :key="email"
            class="wb-cursor"
            :style="{ left: `${pos.x}px`, top: `${pos.y}px`, color: pos.color }"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
              <path d="M0 0 L0 12 L3.5 8.5 L6 13 L7.5 12.3 L5 7 L9 7 Z" />
            </svg>
            <span class="wb-cursor__label" :style="{ background: pos.color }">
              {{ email.split('@')[0] }}
            </span>
          </div>
        </div>

        <!-- ── History panel ──────────────────────────────────────────── -->
        <Transition name="panel">
          <div v-if="showHistory" class="wb-panel">
            <div class="wb-panel__header">
              <span class="font-mono text-xs font-bold uppercase tracking-widest">History</span>
              <button class="wb-panel__close" @click="showHistory = false">
                <Icon name="heroicons:x-mark" class="w-4 h-4" />
              </button>
            </div>

            <div v-if="loadingSnaps" class="wb-panel__empty">
              <div class="wb-spinner" />
            </div>

            <div v-else-if="snapshots.length === 0" class="wb-panel__empty">
              <p class="font-mono text-xs text-[#525252]">No snapshots yet.</p>
              <button v-if="isEditor" class="wb-snap-btn mt-3" @click="saveSnapshot('Manual save')">
                Save now
              </button>
            </div>

            <div v-else class="wb-panel__list">
              <div
                v-for="snap in snapshots"
                :key="snap.id"
                class="wb-snap-item"
              >
                <!-- Thumbnail -->
                <div class="wb-snap-thumb">
                  <img v-if="snap.thumbnail" :src="snap.thumbnail" alt="preview" class="wb-snap-img" />
                  <Icon v-else name="heroicons:photo" class="w-6 h-6 text-[#ccc]" />
                </div>
                <!-- Info -->
                <div class="wb-snap-info">
                  <p class="wb-snap-label">{{ snap.label }}</p>
                  <p class="wb-snap-meta">{{ fmtDate(snap.created_at) }}</p>
                  <p class="wb-snap-meta">{{ snap.saved_by }}</p>
                </div>
                <!-- Actions -->
                <div class="wb-snap-actions">
                  <button
                    v-if="isEditor"
                    class="wb-icon-btn"
                    title="Restore this snapshot"
                    @click="restoreSnapshot(snap)"
                  ><Icon name="heroicons:arrow-path" class="w-3.5 h-3.5" /></button>
                  <button
                    v-if="room?.is_owner"
                    class="wb-icon-btn wb-icon-btn--danger"
                    title="Delete snapshot"
                    @click="deleteSnapshot(snap)"
                  ><Icon name="heroicons:trash" class="w-3.5 h-3.5" /></button>
                </div>
              </div>
            </div>

            <div v-if="isEditor && snapshots.length > 0" class="wb-panel__footer">
              <button class="wb-snap-btn w-full" @click="saveSnapshot('Manual save')">
                Save snapshot now
              </button>
            </div>
          </div>
        </Transition>

        <!-- ── Members panel ──────────────────────────────────────────── -->
        <Transition name="panel">
          <div v-if="showMembers" class="wb-panel">
            <div class="wb-panel__header">
              <span class="font-mono text-xs font-bold uppercase tracking-widest">Members</span>
              <button class="wb-panel__close" @click="showMembers = false">
                <Icon name="heroicons:x-mark" class="w-4 h-4" />
              </button>
            </div>

            <div class="wb-panel__list">
              <!-- Owner -->
              <div class="wb-member-item">
                <span class="wb-member-email">{{ room?.owner_email }}</span>
                <span class="wb-member-role wb-member-role--owner">owner</span>
              </div>
              <!-- Members -->
              <div
                v-for="m in room?.members ?? []"
                :key="m.email"
                class="wb-member-item"
              >
                <span class="wb-member-email">{{ m.email }}</span>
                <span class="wb-member-role">{{ m.role }}</span>
              </div>
              <div v-if="!room?.members?.length" class="wb-panel__empty">
                <p class="font-mono text-xs text-[#525252]">No other members.</p>
              </div>
            </div>

            <div class="wb-panel__footer">
              <NuxtLink
                to="/tools/whiteboard"
                class="wb-snap-btn w-full text-center"
              >Manage in Rooms list ↗</NuxtLink>
            </div>
          </div>
        </Transition>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* ── Page shell ─────────────────────────────────────────────────────────── */
.wb-page {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: #fff;
}

/* ── Error screen ───────────────────────────────────────────────────────── */
.wb-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
}
.wb-error__box {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 2rem;
  border: 3px solid #000;
  max-width: 360px;
}

/* ── Top bar ────────────────────────────────────────────────────────────── */
.wb-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 12px;
  border-bottom: 2px solid #000;
  background: #fff;
  flex-shrink: 0;
  gap: 8px;
  z-index: 20;
}
.wb-topbar__left  { display: flex; align-items: center; gap: 8px; min-width: 0; }
.wb-topbar__center { display: flex; align-items: center; gap: 4px; }
.wb-topbar__right { display: flex; align-items: center; gap: 6px; }

.wb-room-name {
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: 15px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 220px;
}

.wb-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.12em;
  padding: 2px 6px;
  border: 1px solid #000;
}

.wb-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 2px solid #000;
  background: #fff;
  cursor: pointer;
  transition: background 0.1s, color 0.1s;
  flex-shrink: 0;
}
.wb-btn:hover { background: #000; color: #fff; }
.wb-btn--active { background: #000; color: #fff; }
.wb-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.wb-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.wb-dot--on  { background: #22c55e; }
.wb-dot--off { background: #94a3b8; }

.wb-status-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #525252;
  white-space: nowrap;
}

.wb-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  border: 2px solid #fff;
  outline: 1px solid #000;
  cursor: default;
}

.wb-save-msg {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #525252;
  white-space: nowrap;
}

/* ── Canvas area ────────────────────────────────────────────────────────── */
.wb-canvas-area {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.wb-canvas-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 100%;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: #525252;
}

.wb-spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #e5e5e5;
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── Remote cursors ─────────────────────────────────────────────────────── */
.wb-cursors {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 50;
}
.wb-cursor {
  position: absolute;
  transform: translate(-2px, -2px);
  display: flex;
  align-items: flex-start;
  gap: 3px;
}
.wb-cursor__label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #fff;
  padding: 1px 4px;
  white-space: nowrap;
  border-radius: 2px;
  margin-top: 14px;
}

/* ── Side panels ────────────────────────────────────────────────────────── */
.wb-panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 280px;
  background: #fff;
  border-left: 2px solid #000;
  display: flex;
  flex-direction: column;
  z-index: 30;
  overflow: hidden;
}

.wb-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 2px solid #000;
  flex-shrink: 0;
}
.wb-panel__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border: 1px solid transparent;
  transition: border-color 0.1s;
  cursor: pointer;
}
.wb-panel__close:hover { border-color: #000; }

.wb-panel__list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.wb-panel__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 8px;
}

.wb-panel__footer {
  padding: 10px 12px;
  border-top: 2px solid #000;
  flex-shrink: 0;
}

/* Snapshot items */
.wb-snap-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
}
.wb-snap-thumb {
  width: 44px;
  height: 36px;
  border: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  background: #f9f9f9;
}
.wb-snap-img { width: 100%; height: 100%; object-fit: cover; }
.wb-snap-info { flex: 1; min-width: 0; }
.wb-snap-label { font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wb-snap-meta  { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #525252; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wb-snap-actions { display: flex; flex-direction: column; gap: 3px; }
.wb-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 1px solid #000;
  background: #fff;
  cursor: pointer;
  transition: 0.1s;
}
.wb-icon-btn:hover { background: #000; color: #fff; }
.wb-icon-btn--danger { border-color: #dc2626; color: #dc2626; }
.wb-icon-btn--danger:hover { background: #dc2626; color: #fff; }

.wb-snap-btn {
  display: block;
  padding: 6px 12px;
  border: 2px solid #000;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  cursor: pointer;
  background: #fff;
  transition: 0.1s;
  text-decoration: none;
  color: #000;
}
.wb-snap-btn:hover { background: #000; color: #fff; }

/* Members */
.wb-member-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
}
.wb-member-email { font-family: 'JetBrains Mono', monospace; font-size: 11px; overflow: hidden; text-overflow: ellipsis; }
.wb-member-role { font-family: 'JetBrains Mono', monospace; font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em; padding: 2px 5px; border: 1px solid #000; white-space: nowrap; flex-shrink: 0; }
.wb-member-role--owner { background: #000; color: #fff; }

/* Panel slide transition */
.panel-enter-active, .panel-leave-active { transition: transform 0.15s ease; }
.panel-enter-from, .panel-leave-to { transform: translateX(100%); }
</style>
