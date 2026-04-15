<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const config = useRuntimeConfig()
const apiBase = config.public.apiBase

const tokenCookie = useCookie('ocr_token')
const userCookie  = useCookie('ocr_user')

const authHeader = computed(() => ({
  Authorization: `Bearer ${tokenCookie.value}`,
  'Content-Type': 'application/json',
}))

const currentUser = computed(() => {
  try { return JSON.parse(userCookie.value as string) } catch { return null }
})

// ── State ──────────────────────────────────────────────────────────────────
interface Project {
  id: string
  name: string
  description: string
  owner_email: string
  is_public: boolean
  member_count: number
  created_at: string
  updated_at: string
}

const projects = ref<Project[]>([])
const loading  = ref(true)
const error    = ref('')

// Create modal
const showCreate  = ref(false)
const newName     = ref('')
const newDesc     = ref('')
const newPublic   = ref(false)
const creating    = ref(false)

// Delete confirm
const deleteTarget = ref<Project | null>(null)
const deleting     = ref(false)

// ── Fetch ──────────────────────────────────────────────────────────────────
async function fetchProjects() {
  loading.value = true
  error.value   = ''
  try {
    const data = await $fetch<Project[]>(`${apiBase}/api/projects`, { headers: authHeader.value })
    projects.value = data
  } catch (e: any) {
    error.value = e?.data?.detail ?? 'Failed to load projects'
  } finally {
    loading.value = false
  }
}

// ── Create ─────────────────────────────────────────────────────────────────
async function createProject() {
  if (!newName.value.trim()) return
  creating.value = true
  try {
    const proj = await $fetch<Project>(`${apiBase}/api/projects`, {
      method: 'POST',
      headers: authHeader.value,
      body: { name: newName.value.trim(), description: newDesc.value.trim(), is_public: newPublic.value },
    })
    projects.value.unshift(proj)
    showCreate.value = false
    newName.value = ''
    newDesc.value = ''
    newPublic.value = false
    // Open project immediately
    navigateTo(`/tools/project/${proj.id}`)
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to create project')
  } finally {
    creating.value = false
  }
}

// ── Delete ─────────────────────────────────────────────────────────────────
async function confirmDelete(p: Project) {
  deleteTarget.value = p
}
async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await $fetch(`${apiBase}/api/projects/${deleteTarget.value.id}`, {
      method: 'DELETE',
      headers: authHeader.value,
    })
    projects.value = projects.value.filter(p => p.id !== deleteTarget.value!.id)
    deleteTarget.value = null
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to delete project')
  } finally {
    deleting.value = false
  }
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' })
}

onMounted(fetchProjects)
</script>

<template>
  <div class="min-h-screen bg-[#FFFDF5] p-6 md:p-10">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-black text-black uppercase tracking-tight">Project Management</h1>
        <p class="text-gray-600 mt-1">Kelola proyek, task, dan timeline timmu.</p>
      </div>
      <button
        @click="showCreate = true"
        class="flex items-center gap-2 px-5 py-3 bg-black text-white font-bold uppercase text-sm border-4 border-black shadow-[4px_4px_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_#000] transition-all"
      >
        <Icon name="heroicons:plus" class="w-5 h-5" />
        New Project
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="text-center py-24 text-gray-500 font-bold">Loading projects...</div>

    <!-- Error -->
    <div v-else-if="error" class="bg-red-100 border-4 border-red-600 p-4 font-bold text-red-700">{{ error }}</div>

    <!-- Empty -->
    <div
      v-else-if="projects.length === 0"
      class="text-center py-24 border-4 border-dashed border-gray-300"
    >
      <Icon name="heroicons:clipboard-document-list" class="w-16 h-16 mx-auto text-gray-300 mb-4" />
      <p class="text-xl font-black text-gray-400 uppercase">No projects yet</p>
      <p class="text-gray-400 mt-2">Create your first project to get started.</p>
    </div>

    <!-- Grid -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      <NuxtLink
        v-for="p in projects"
        :key="p.id"
        :to="`/tools/project/${p.id}`"
        class="block bg-white border-4 border-black shadow-[4px_4px_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_#000] transition-all group"
      >
        <div class="p-5">
          <!-- Top row -->
          <div class="flex items-start justify-between mb-3">
            <div class="w-10 h-10 bg-blue-500 border-2 border-black flex items-center justify-center">
              <Icon name="heroicons:folder" class="w-5 h-5 text-white" />
            </div>
            <div class="flex items-center gap-1">
              <span
                v-if="p.is_public"
                class="text-xs font-bold px-2 py-0.5 bg-green-200 border-2 border-black text-black uppercase"
              >Public</span>
              <span
                v-if="p.owner_email === currentUser?.email"
                class="text-xs font-bold px-2 py-0.5 bg-yellow-300 border-2 border-black text-black uppercase"
              >Owner</span>
            </div>
          </div>

          <h3 class="font-black text-black text-lg leading-tight mb-1 line-clamp-2">{{ p.name }}</h3>
          <p class="text-sm text-gray-500 line-clamp-2 mb-4 min-h-[2.5rem]">{{ p.description || 'No description' }}</p>

          <div class="flex items-center justify-between text-xs text-gray-500 font-bold border-t-2 border-gray-200 pt-3">
            <span class="flex items-center gap-1">
              <Icon name="heroicons:users" class="w-3.5 h-3.5" />
              {{ p.member_count }} member{{ p.member_count !== 1 ? 's' : '' }}
            </span>
            <span>{{ formatDate(p.updated_at ?? p.created_at) }}</span>
          </div>
        </div>

        <!-- Delete (only owner) -->
        <div
          v-if="p.owner_email === currentUser?.email"
          class="border-t-4 border-black px-5 py-2 bg-gray-50 flex justify-end opacity-0 group-hover:opacity-100 transition-opacity"
          @click.prevent.stop="confirmDelete(p)"
        >
          <button class="text-xs font-bold text-red-600 hover:underline uppercase flex items-center gap-1">
            <Icon name="heroicons:trash" class="w-3.5 h-3.5" />
            Delete
          </button>
        </div>
      </NuxtLink>
    </div>

    <!-- ── Create Modal ─────────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="showCreate"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="showCreate = false"
      >
        <div class="bg-white border-4 border-black shadow-[8px_8px_0_#000] w-full max-w-md">
          <div class="bg-black text-white px-6 py-4 flex items-center justify-between">
            <h2 class="font-black uppercase text-lg">New Project</h2>
            <button @click="showCreate = false" class="text-white hover:text-yellow-300">
              <Icon name="heroicons:x-mark" class="w-6 h-6" />
            </button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-sm font-black uppercase mb-1">Project Name *</label>
              <input
                v-model="newName"
                type="text"
                placeholder="My Awesome Project"
                class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none focus:bg-yellow-50"
                @keydown.enter="createProject"
              />
            </div>
            <div>
              <label class="block text-sm font-black uppercase mb-1">Description</label>
              <textarea
                v-model="newDesc"
                rows="3"
                placeholder="What is this project about?"
                class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none focus:bg-yellow-50 resize-none"
              />
            </div>
            <label class="flex items-center gap-3 cursor-pointer select-none">
              <input v-model="newPublic" type="checkbox" class="w-5 h-5 border-4 border-black accent-black" />
              <span class="font-bold text-sm">Public (anyone with link can view)</span>
            </label>
          </div>
          <div class="px-6 pb-6 flex gap-3">
            <button
              @click="showCreate = false"
              class="flex-1 py-3 border-4 border-black font-black uppercase hover:bg-gray-100 transition-colors"
            >Cancel</button>
            <button
              @click="createProject"
              :disabled="creating || !newName.trim()"
              class="flex-1 py-3 bg-black text-white font-black uppercase border-4 border-black disabled:opacity-50 hover:bg-gray-900 transition-colors"
            >{{ creating ? 'Creating...' : 'Create' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Delete Confirm Modal ─────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="deleteTarget"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="deleteTarget = null"
      >
        <div class="bg-white border-4 border-black shadow-[8px_8px_0_#000] w-full max-w-sm">
          <div class="bg-red-600 text-white px-6 py-4">
            <h2 class="font-black uppercase text-lg">Delete Project?</h2>
          </div>
          <div class="p-6">
            <p class="font-bold">Are you sure you want to delete <strong>"{{ deleteTarget.name }}"</strong>? This will permanently remove all tasks and data.</p>
          </div>
          <div class="px-6 pb-6 flex gap-3">
            <button
              @click="deleteTarget = null"
              class="flex-1 py-3 border-4 border-black font-black uppercase hover:bg-gray-100"
            >Cancel</button>
            <button
              @click="doDelete"
              :disabled="deleting"
              class="flex-1 py-3 bg-red-600 text-white font-black uppercase border-4 border-black disabled:opacity-50"
            >{{ deleting ? 'Deleting...' : 'Delete' }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
