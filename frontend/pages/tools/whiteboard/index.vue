<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const config = useRuntimeConfig()
const apiBase = config.public.apiBase

// ── Auth token from cookie ────────────────────────────────────────────────
const tokenCookie = useCookie('ocr_token')
const userCookie  = useCookie('ocr_user')

const authHeader = computed(() => ({
  Authorization: `Bearer ${tokenCookie.value}`,
  'Content-Type': 'application/json',
}))

const currentUser = computed(() => {
  try { return JSON.parse(userCookie.value as string) } catch { return null }
})

// ── State ─────────────────────────────────────────────────────────────────
interface Room {
  id: string
  name: string
  description: string
  owner_email: string
  is_owner: boolean
  is_public: boolean
  share_token: string
  members: { email: string; role: string }[]
  created_at: string
  updated_at: string
}

const ownedRooms  = ref<Room[]>([])
const sharedRooms = ref<Room[]>([])
const loading     = ref(true)
const error       = ref('')

// Create room modal
const showCreate  = ref(false)
const newName     = ref('')
const newDesc     = ref('')
const newPublic   = ref(false)
const creating    = ref(false)

// Invite member modal
const showInvite  = ref(false)
const inviteRoom  = ref<Room | null>(null)
const inviteEmail = ref('')
const inviteRole  = ref<'editor' | 'viewer'>('editor')
const inviting    = ref(false)

// Delete confirm
const deleteTarget = ref<Room | null>(null)
const deleting     = ref(false)

// ── API helpers ───────────────────────────────────────────────────────────
async function fetchRooms() {
  loading.value = true
  error.value   = ''
  try {
    const res = await fetch(`${apiBase}/api/v1/whiteboard/rooms`, {
      headers: authHeader.value,
    })
    if (!res.ok) throw new Error(await res.text())
    const data = await res.json()
    ownedRooms.value  = data.owned  ?? []
    sharedRooms.value = data.shared ?? []
  } catch (e: any) {
    error.value = e?.message || 'Failed to load rooms'
  } finally {
    loading.value = false
  }
}

async function createRoom() {
  if (!newName.value.trim()) return
  creating.value = true
  try {
    const res = await fetch(`${apiBase}/api/v1/whiteboard/rooms`, {
      method: 'POST',
      headers: authHeader.value,
      body: JSON.stringify({
        name: newName.value.trim(),
        description: newDesc.value.trim(),
        is_public: newPublic.value,
      }),
    })
    if (!res.ok) throw new Error(await res.text())
    const room = await res.json()
    ownedRooms.value.unshift(room)
    showCreate.value = false
    newName.value    = ''
    newDesc.value    = ''
    newPublic.value  = false
    // Open the new room immediately in this tab
    navigateTo(`/tools/whiteboard/${room.id}`)
  } catch (e: any) {
    alert(e?.message || 'Failed to create room')
  } finally {
    creating.value = false
  }
}

async function deleteRoom() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    const res = await fetch(`${apiBase}/api/v1/whiteboard/rooms/${deleteTarget.value.id}`, {
      method: 'DELETE',
      headers: authHeader.value,
    })
    if (!res.ok && res.status !== 204) throw new Error(await res.text())
    ownedRooms.value  = ownedRooms.value.filter(r => r.id !== deleteTarget.value!.id)
    deleteTarget.value = null
  } catch (e: any) {
    alert(e?.message || 'Failed to delete room')
  } finally {
    deleting.value = false
  }
}

async function inviteMember() {
  if (!inviteRoom.value || !inviteEmail.value.trim()) return
  inviting.value = true
  try {
    const res = await fetch(`${apiBase}/api/v1/whiteboard/rooms/${inviteRoom.value.id}/members`, {
      method: 'POST',
      headers: authHeader.value,
      body: JSON.stringify({ email: inviteEmail.value.trim(), role: inviteRole.value }),
    })
    if (!res.ok) throw new Error(await res.text())
    await fetchRooms()
    showInvite.value  = false
    inviteEmail.value = ''
  } catch (e: any) {
    alert(e?.message || 'Failed to invite member')
  } finally {
    inviting.value = false
  }
}

async function removeMember(room: Room, email: string) {
  if (!confirm(`Remove ${email} from "${room.name}"?`)) return
  try {
    await fetch(`${apiBase}/api/v1/whiteboard/rooms/${room.id}/members/${encodeURIComponent(email)}`, {
      method: 'DELETE',
      headers: authHeader.value,
    })
    await fetchRooms()
  } catch (e: any) {
    alert(e?.message || 'Failed to remove member')
  }
}

// ── Open room in same tab (already in new tab from dashboard) ─────────────
function openRoom(room: Room) {
  navigateTo(`/tools/whiteboard/${room.id}`)
}

function copyShareLink(room: Room) {
  const url = `${window.location.origin}/tools/whiteboard/${room.id}`
  navigator.clipboard.writeText(url)
    .then(() => alert('Link copied!'))
}

// ── Formatting ────────────────────────────────────────────────────────────
function timeAgo(iso: string) {
  if (!iso) return ''
  const d = new Date(iso)
  const diff = Math.floor((Date.now() - d.getTime()) / 1000)
  if (diff < 60)    return 'just now'
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

onMounted(fetchRooms)
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-10 pb-8 border-b-4 border-[var(--foreground)]">
      <div class="flex items-start justify-between">
        <div>
          <h1 class="font-serif text-4xl md:text-5xl font-bold tracking-tighter">WHITEBOARD</h1>
          <p class="text-[var(--muted-foreground)] mt-2">
            Collaborative drawing rooms — opens full screen
          </p>
        </div>
        <button
          class="flex items-center gap-2 px-5 py-2 border-2 border-[var(--foreground)] bg-[var(--foreground)] text-[var(--background)] hover:bg-[var(--background)] hover:text-[var(--foreground)] transition-colors font-mono text-sm font-bold"
          @click="showCreate = true"
        >
          <Icon name="heroicons:plus" class="w-4 h-4" />
          NEW ROOM
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center gap-3 py-16 text-[var(--muted-foreground)] font-mono text-sm">
      <div class="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      Loading rooms…
    </div>

    <!-- Error -->
    <div v-else-if="error" class="border-2 border-red-500 p-6 text-red-600 font-mono text-sm">
      {{ error }}
    </div>

    <template v-else>
      <!-- My Rooms -->
      <section class="mb-12">
        <h2 class="font-mono text-xs tracking-[0.2em] uppercase text-[var(--muted-foreground)] mb-4">
          MY ROOMS ({{ ownedRooms.length }})
        </h2>

        <div v-if="ownedRooms.length === 0" class="border-2 border-dashed border-[var(--muted-foreground)] p-12 text-center">
          <p class="font-mono text-sm text-[var(--muted-foreground)]">No rooms yet.</p>
          <button
            class="mt-4 px-4 py-2 border-2 border-[var(--foreground)] font-mono text-sm hover:bg-[var(--foreground)] hover:text-[var(--background)] transition-colors"
            @click="showCreate = true"
          >Create your first room</button>
        </div>

        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="room in ownedRooms"
            :key="room.id"
            class="border-2 border-[var(--foreground)] p-6 flex flex-col gap-4"
          >
            <!-- Room info -->
            <div class="flex items-start justify-between gap-2">
              <div class="flex-1 min-w-0">
                <h3 class="font-serif text-lg font-bold truncate">{{ room.name }}</h3>
                <p v-if="room.description" class="text-xs text-[var(--muted-foreground)] mt-1 line-clamp-2">
                  {{ room.description }}
                </p>
              </div>
              <span
                v-if="room.is_public"
                class="shrink-0 px-2 py-0.5 border border-[var(--foreground)] font-mono text-[10px] uppercase"
              >Public</span>
            </div>

            <!-- Meta -->
            <div class="flex items-center gap-4 font-mono text-xs text-[var(--muted-foreground)]">
              <span class="flex items-center gap-1">
                <Icon name="heroicons:users" class="w-3 h-3" />
                {{ room.members.length + 1 }} member{{ room.members.length !== 0 ? 's' : '' }}
              </span>
              <span>Updated {{ timeAgo(room.updated_at) }}</span>
            </div>

            <!-- Actions -->
            <div class="flex gap-2 mt-auto pt-2 border-t border-[var(--muted-foreground)] border-opacity-30">
              <button
                class="flex-1 py-2 border-2 border-[var(--foreground)] bg-[var(--foreground)] text-[var(--background)] font-mono text-xs font-bold hover:bg-[var(--background)] hover:text-[var(--foreground)] transition-colors"
                @click="openRoom(room)"
              >OPEN</button>
              <button
                class="px-3 py-2 border-2 border-[var(--foreground)] font-mono text-xs hover:bg-[var(--foreground)] hover:text-[var(--background)] transition-colors"
                title="Copy share link"
                @click="copyShareLink(room)"
              ><Icon name="heroicons:link" class="w-4 h-4" /></button>
              <button
                class="px-3 py-2 border-2 border-[var(--foreground)] font-mono text-xs hover:bg-[var(--foreground)] hover:text-[var(--background)] transition-colors"
                title="Invite member"
                @click="inviteRoom = room; inviteEmail = ''; showInvite = true"
              ><Icon name="heroicons:user-plus" class="w-4 h-4" /></button>
              <button
                class="px-3 py-2 border-2 border-red-500 text-red-500 font-mono text-xs hover:bg-red-500 hover:text-white transition-colors"
                title="Delete room"
                @click="deleteTarget = room"
              ><Icon name="heroicons:trash" class="w-4 h-4" /></button>
            </div>
          </div>
        </div>
      </section>

      <!-- Shared with me -->
      <section v-if="sharedRooms.length > 0">
        <h2 class="font-mono text-xs tracking-[0.2em] uppercase text-[var(--muted-foreground)] mb-4">
          SHARED WITH ME ({{ sharedRooms.length }})
        </h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="room in sharedRooms"
            :key="room.id"
            class="border-2 border-[var(--foreground)] p-6 flex flex-col gap-4"
          >
            <div class="flex-1">
              <h3 class="font-serif text-lg font-bold truncate">{{ room.name }}</h3>
              <p class="font-mono text-xs text-[var(--muted-foreground)] mt-1">by {{ room.owner_email }}</p>
              <p v-if="room.description" class="text-xs text-[var(--muted-foreground)] mt-2 line-clamp-2">
                {{ room.description }}
              </p>
            </div>
            <div class="flex gap-2 pt-2 border-t border-[var(--muted-foreground)] border-opacity-30">
              <button
                class="flex-1 py-2 border-2 border-[var(--foreground)] font-mono text-xs font-bold hover:bg-[var(--foreground)] hover:text-[var(--background)] transition-colors"
                @click="openRoom(room)"
              >OPEN</button>
            </div>
          </div>
        </div>
      </section>
    </template>

    <!-- ── Create Room Modal ──────────────────────────────────────────── -->
    <Teleport to="body">
      <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
        <div class="modal-box">
          <div class="modal-header">
            <h2 class="font-serif text-2xl font-bold">New Whiteboard Room</h2>
            <button class="modal-close" @click="showCreate = false">
              <Icon name="heroicons:x-mark" class="w-5 h-5" />
            </button>
          </div>

          <div class="modal-body">
            <label class="field-label">Room Name *</label>
            <input
              v-model="newName"
              type="text"
              class="field-input"
              placeholder="e.g. Sprint Planning Board"
              @keydown.enter="createRoom"
            />

            <label class="field-label mt-4">Description</label>
            <textarea
              v-model="newDesc"
              class="field-input resize-none"
              rows="2"
              placeholder="Optional short description"
            />

            <label class="flex items-center gap-3 mt-4 cursor-pointer">
              <input v-model="newPublic" type="checkbox" class="w-4 h-4" />
              <span class="font-mono text-sm">Public (anyone with link can view)</span>
            </label>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="showCreate = false">Cancel</button>
            <button
              class="btn-primary"
              :disabled="!newName.trim() || creating"
              @click="createRoom"
            >
              <span v-if="creating">Creating…</span>
              <span v-else>Create &amp; Open</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Invite Modal -->
      <div v-if="showInvite" class="modal-overlay" @click.self="showInvite = false">
        <div class="modal-box">
          <div class="modal-header">
            <h2 class="font-serif text-xl font-bold">Invite to "{{ inviteRoom?.name }}"</h2>
            <button class="modal-close" @click="showInvite = false">
              <Icon name="heroicons:x-mark" class="w-5 h-5" />
            </button>
          </div>
          <div class="modal-body">
            <label class="field-label">Email</label>
            <input
              v-model="inviteEmail"
              type="email"
              class="field-input"
              placeholder="user@lman.id"
            />
            <label class="field-label mt-4">Role</label>
            <div class="flex gap-3 mt-1">
              <label class="flex items-center gap-2 cursor-pointer font-mono text-sm">
                <input v-model="inviteRole" type="radio" value="editor" />
                Editor
              </label>
              <label class="flex items-center gap-2 cursor-pointer font-mono text-sm">
                <input v-model="inviteRole" type="radio" value="viewer" />
                Viewer (read only)
              </label>
            </div>

            <!-- Existing members -->
            <div v-if="inviteRoom && inviteRoom.members.length > 0" class="mt-6">
              <p class="font-mono text-xs text-[var(--muted-foreground)] uppercase tracking-widest mb-2">Current Members</p>
              <div
                v-for="m in inviteRoom.members"
                :key="m.email"
                class="flex items-center justify-between py-2 border-b border-[var(--muted-foreground)] border-opacity-20"
              >
                <span class="font-mono text-sm">{{ m.email }}</span>
                <div class="flex items-center gap-3">
                  <span class="font-mono text-xs text-[var(--muted-foreground)] uppercase">{{ m.role }}</span>
                  <button
                    class="text-red-500 hover:text-red-700"
                    @click="removeMember(inviteRoom!, m.email)"
                  ><Icon name="heroicons:x-mark" class="w-4 h-4" /></button>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showInvite = false">Close</button>
            <button class="btn-primary" :disabled="!inviteEmail.trim() || inviting" @click="inviteMember">
              <span v-if="inviting">Inviting…</span>
              <span v-else>Invite</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Delete Confirm -->
      <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
        <div class="modal-box">
          <div class="modal-header">
            <h2 class="font-serif text-xl font-bold">Delete Room?</h2>
          </div>
          <div class="modal-body">
            <p class="font-mono text-sm">
              "<strong>{{ deleteTarget.name }}</strong>" and all its history will be permanently deleted.
            </p>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="deleteTarget = null">Cancel</button>
            <button class="btn-danger" :disabled="deleting" @click="deleteRoom">
              <span v-if="deleting">Deleting…</span>
              <span v-else>Delete</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}
.modal-box {
  background: #fff;
  border: 3px solid #000;
  width: 100%;
  max-width: 480px;
  display: flex;
  flex-direction: column;
}
.modal-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 2px solid #000;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.modal-close {
  padding: 0.25rem;
  border: 1px solid transparent;
  transition: border-color 0.1s;
}
.modal-close:hover { border-color: #000; }
.modal-body { padding: 1.5rem; display: flex; flex-direction: column; }
.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 2px solid #000;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}
.field-label { font-family: 'JetBrains Mono', monospace; font-size: 11px; text-transform: uppercase; letter-spacing: 0.12em; color: #525252; margin-bottom: 4px; display: block; }
.field-input { width: 100%; border: 2px solid #000; padding: 0.5rem 0.75rem; font-family: 'JetBrains Mono', monospace; font-size: 13px; outline: none; background: #fff; }
.field-input:focus { outline: 2px solid #000; outline-offset: 1px; }
.btn-primary { padding: 0.5rem 1.25rem; background: #000; color: #fff; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; border: 2px solid #000; cursor: pointer; transition: 0.1s; }
.btn-primary:hover:not(:disabled) { background: #fff; color: #000; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { padding: 0.5rem 1.25rem; background: #fff; color: #000; font-family: 'JetBrains Mono', monospace; font-size: 12px; border: 2px solid #000; cursor: pointer; transition: 0.1s; }
.btn-secondary:hover { background: #f5f5f5; }
.btn-danger { padding: 0.5rem 1.25rem; background: #dc2626; color: #fff; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; border: 2px solid #dc2626; cursor: pointer; transition: 0.1s; }
.btn-danger:hover:not(:disabled) { background: #fff; color: #dc2626; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
