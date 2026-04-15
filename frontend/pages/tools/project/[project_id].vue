<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const route  = useRoute()
const config = useRuntimeConfig()
const apiBase = config.public.apiBase
const projectId = route.params.project_id as string

const tokenCookie = useCookie('ocr_token')
const userCookie  = useCookie('ocr_user')

const authHeader = computed(() => ({
  Authorization: `Bearer ${tokenCookie.value}`,
  'Content-Type': 'application/json',
}))

const currentUser = computed(() => {
  try { return JSON.parse(userCookie.value as string) } catch { return null }
})

// ── Types ──────────────────────────────────────────────────────────────────
interface Member { email: string; role: string; joined_at: string }
interface Comment { id: string; author_email: string; body: string; created_at: string }
interface Task {
  id: string; project_id: string; column_id: string
  title: string; description: string
  assignee_email: string | null; priority: string
  due_date: string | null; start_date: string | null
  position: number; color: string
  created_at: string; updated_at: string | null
  created_by: string | null; comment_count: number
}
interface Column { id: string; project_id: string; name: string; position: number; color: string; tasks: Task[] }
interface Project {
  id: string; name: string; description: string
  owner_email: string; is_public: boolean
  created_at: string; updated_at: string | null
  member_count: number; columns: Column[]; members: Member[]
}

// ── State ──────────────────────────────────────────────────────────────────
const project  = ref<Project | null>(null)
const loading  = ref(true)
const error    = ref('')
const activeView = ref<'board' | 'gantt'>('board')

// Task modal
const taskModal   = ref(false)
const editingTask = ref<Task | null>(null)  // null = create new
const taskColumn  = ref<Column | null>(null)
const taskForm    = reactive({
  title: '', description: '', assignee_email: '', priority: 'medium',
  due_date: '', start_date: '', color: '#3B82F6',
})
const savingTask  = ref(false)

// Task detail panel
const detailTask  = ref<Task | null>(null)
const comments    = ref<Comment[]>([])
const newComment  = ref('')
const postingComment = ref(false)

// Column modal
const addColModal  = ref(false)
const newColName   = ref('')
const newColColor  = ref('#6B7280')
const addingCol    = ref(false)

// Members panel
const showMembers = ref(false)
const inviteEmail = ref('')
const inviteRole  = ref<'editor' | 'viewer'>('editor')
const inviting    = ref(false)

// Settings modal
const showSettings = ref(false)
const settingsForm = reactive({ name: '', description: '', is_public: false })
const savingSettings = ref(false)

// Dragging
const dragTask   = ref<{ task: Task; fromColId: string } | null>(null)
const dragOverCol = ref<string | null>(null)

// Gantt ref
const ganttEl   = ref<HTMLElement | null>(null)
let ganttChart: any = null

// ── Data loading ───────────────────────────────────────────────────────────
async function fetchProject() {
  loading.value = true
  error.value   = ''
  try {
    const data = await $fetch<Project>(`${apiBase}/api/projects/${projectId}`, { headers: authHeader.value })
    project.value = data
    if (Object.keys(settingsForm).length) {
      settingsForm.name        = data.name
      settingsForm.description = data.description
      settingsForm.is_public   = data.is_public
    }
  } catch (e: any) {
    error.value = e?.data?.detail ?? 'Failed to load project'
  } finally {
    loading.value = false
  }
}

// ── Permission helpers ─────────────────────────────────────────────────────
const isOwner = computed(() => project.value?.owner_email === currentUser.value?.email)
const isEditor = computed(() => {
  if (!project.value || !currentUser.value) return false
  if (isOwner.value) return true
  const m = project.value.members.find(m => m.email === currentUser.value.email)
  return m?.role === 'editor'
})

// ── Task CRUD ──────────────────────────────────────────────────────────────
function openCreateTask(col: Column) {
  editingTask.value = null
  taskColumn.value  = col
  Object.assign(taskForm, { title: '', description: '', assignee_email: '', priority: 'medium', due_date: '', start_date: '', color: '#3B82F6' })
  taskModal.value = true
}
function openEditTask(task: Task) {
  editingTask.value = task
  taskColumn.value  = project.value!.columns.find(c => c.id === task.column_id) ?? null
  Object.assign(taskForm, {
    title: task.title,
    description: task.description,
    assignee_email: task.assignee_email ?? '',
    priority: task.priority,
    due_date: task.due_date ? task.due_date.slice(0, 10) : '',
    start_date: task.start_date ? task.start_date.slice(0, 10) : '',
    color: task.color,
  })
  taskModal.value = true
}
async function saveTask() {
  if (!taskForm.title.trim()) return
  savingTask.value = true
  try {
    const body: any = {
      title: taskForm.title.trim(),
      description: taskForm.description,
      assignee_email: taskForm.assignee_email || null,
      priority: taskForm.priority,
      due_date: taskForm.due_date ? new Date(taskForm.due_date).toISOString() : null,
      start_date: taskForm.start_date ? new Date(taskForm.start_date).toISOString() : null,
      color: taskForm.color,
    }
    if (editingTask.value) {
      const updated = await $fetch<Task>(`${apiBase}/api/projects/${projectId}/tasks/${editingTask.value.id}`, {
        method: 'PATCH', headers: authHeader.value, body,
      })
      replaceTask(updated)
    } else {
      const col = taskColumn.value!
      body.column_id = col.id
      body.position  = col.tasks.length
      const created = await $fetch<Task>(`${apiBase}/api/projects/${projectId}/tasks`, {
        method: 'POST', headers: authHeader.value, body,
      })
      col.tasks.push(created)
    }
    taskModal.value = false
    if (activeView.value === 'gantt') nextTick(renderGantt)
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to save task')
  } finally {
    savingTask.value = false
  }
}
function replaceTask(updated: Task) {
  for (const col of project.value!.columns) {
    const idx = col.tasks.findIndex(t => t.id === updated.id)
    if (idx !== -1) { col.tasks[idx] = updated; break }
  }
}
async function deleteTask(task: Task) {
  if (!confirm(`Delete task "${task.title}"?`)) return
  try {
    await $fetch(`${apiBase}/api/projects/${projectId}/tasks/${task.id}`, { method: 'DELETE', headers: authHeader.value })
    for (const col of project.value!.columns) {
      const idx = col.tasks.findIndex(t => t.id === task.id)
      if (idx !== -1) { col.tasks.splice(idx, 1); break }
    }
    if (detailTask.value?.id === task.id) detailTask.value = null
    if (activeView.value === 'gantt') nextTick(renderGantt)
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to delete task')
  }
}

// ── Drag & Drop ────────────────────────────────────────────────────────────
function onDragStart(task: Task, fromColId: string) {
  dragTask.value = { task, fromColId }
}
function onDragOver(e: DragEvent, colId: string) {
  e.preventDefault()
  dragOverCol.value = colId
}
function onDragLeave() {
  dragOverCol.value = null
}
async function onDrop(e: DragEvent, col: Column) {
  e.preventDefault()
  dragOverCol.value = null
  if (!dragTask.value) return
  const { task, fromColId } = dragTask.value
  dragTask.value = null
  if (task.column_id === col.id) return

  // Optimistic update
  const fromCol = project.value!.columns.find(c => c.id === fromColId)!
  fromCol.tasks = fromCol.tasks.filter(t => t.id !== task.id)
  task.column_id = col.id
  task.position  = col.tasks.length
  col.tasks.push(task)

  try {
    await $fetch(`${apiBase}/api/projects/${projectId}/tasks/${task.id}/move`, {
      method: 'POST', headers: authHeader.value,
      body: { column_id: col.id, position: task.position },
    })
    if (activeView.value === 'gantt') nextTick(renderGantt)
  } catch (e: any) {
    alert('Failed to move task — reloading')
    fetchProject()
  }
}

// ── Column CRUD ────────────────────────────────────────────────────────────
async function addColumn() {
  if (!newColName.value.trim()) return
  addingCol.value = true
  try {
    const col = await $fetch<Column>(`${apiBase}/api/projects/${projectId}/columns`, {
      method: 'POST', headers: authHeader.value,
      body: { name: newColName.value.trim(), position: project.value!.columns.length, color: newColColor.value },
    })
    project.value!.columns.push(col)
    addColModal.value = false
    newColName.value = ''
    newColColor.value = '#6B7280'
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to add column')
  } finally {
    addingCol.value = false
  }
}
async function deleteColumn(col: Column) {
  if (col.tasks.length > 0 && !confirm(`Delete column "${col.name}" and its ${col.tasks.length} task(s)?`)) return
  if (col.tasks.length === 0 && !confirm(`Delete column "${col.name}"?`)) return
  try {
    await $fetch(`${apiBase}/api/projects/${projectId}/columns/${col.id}`, { method: 'DELETE', headers: authHeader.value })
    project.value!.columns = project.value!.columns.filter(c => c.id !== col.id)
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to delete column')
  }
}

// ── Comments ───────────────────────────────────────────────────────────────
async function openDetail(task: Task) {
  detailTask.value = task
  await loadComments(task.id)
}
async function loadComments(taskId: string) {
  try {
    comments.value = await $fetch<Comment[]>(
      `${apiBase}/api/projects/${projectId}/tasks/${taskId}/comments`,
      { headers: authHeader.value }
    )
  } catch { comments.value = [] }
}
async function postComment() {
  if (!newComment.value.trim() || !detailTask.value) return
  postingComment.value = true
  try {
    const c = await $fetch<Comment>(
      `${apiBase}/api/projects/${projectId}/tasks/${detailTask.value.id}/comments`,
      { method: 'POST', headers: authHeader.value, body: { body: newComment.value.trim() } }
    )
    comments.value.push(c)
    newComment.value = ''
    detailTask.value.comment_count++
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to post comment')
  } finally {
    postingComment.value = false
  }
}
async function deleteComment(c: Comment) {
  try {
    await $fetch(`${apiBase}/api/projects/${projectId}/tasks/${detailTask.value!.id}/comments/${c.id}`, {
      method: 'DELETE', headers: authHeader.value,
    })
    comments.value = comments.value.filter(x => x.id !== c.id)
    detailTask.value!.comment_count--
  } catch {}
}

// ── Members ────────────────────────────────────────────────────────────────
async function inviteMember() {
  if (!inviteEmail.value.trim()) return
  inviting.value = true
  try {
    await $fetch(`${apiBase}/api/projects/${projectId}/members`, {
      method: 'POST', headers: authHeader.value,
      body: { email: inviteEmail.value.trim(), role: inviteRole.value },
    })
    inviteEmail.value = ''
    await fetchProject()
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to invite member')
  } finally {
    inviting.value = false
  }
}
async function removeMember(email: string) {
  if (!confirm(`Remove ${email} from project?`)) return
  try {
    await $fetch(`${apiBase}/api/projects/${projectId}/members/${encodeURIComponent(email)}`, {
      method: 'DELETE', headers: authHeader.value,
    })
    await fetchProject()
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to remove member')
  }
}

// ── Settings ───────────────────────────────────────────────────────────────
async function saveSettings() {
  savingSettings.value = true
  try {
    const updated = await $fetch<Project>(`${apiBase}/api/projects/${projectId}`, {
      method: 'PATCH', headers: authHeader.value,
      body: { name: settingsForm.name, description: settingsForm.description, is_public: settingsForm.is_public },
    })
    project.value!.name        = updated.name
    project.value!.description = updated.description
    project.value!.is_public   = updated.is_public
    showSettings.value = false
  } catch (e: any) {
    alert(e?.data?.detail ?? 'Failed to save settings')
  } finally {
    savingSettings.value = false
  }
}

// ── Gantt ──────────────────────────────────────────────────────────────────
function allTasks(): Task[] {
  return project.value?.columns.flatMap(c => c.tasks) ?? []
}

async function renderGantt() {
  if (!ganttEl.value || !project.value) return
  const tasks = allTasks().filter(t => t.start_date && t.due_date)
  if (tasks.length === 0) {
    ganttEl.value.innerHTML = '<div class="flex items-center justify-center h-full text-gray-400 font-bold uppercase text-sm">No tasks with start & due dates for Gantt</div>'
    ganttChart = null
    return
  }
  ganttEl.value.innerHTML = ''
  const { default: Gantt } = await import('frappe-gantt')
  const ganttTasks = tasks.map(t => ({
    id: t.id,
    name: t.title,
    start: t.start_date!.slice(0, 10),
    end: t.due_date!.slice(0, 10),
    progress: 0,
    custom_class: `priority-${t.priority}`,
  }))
  ganttChart = new Gantt(ganttEl.value, ganttTasks, {
    view_mode: 'Week',
    date_format: 'YYYY-MM-DD',
    on_click: (ganttTask: any) => {
      const task = allTasks().find(t => t.id === ganttTask.id)
      if (task) openDetail(task)
    },
  })
}

watch(activeView, (v) => {
  if (v === 'gantt') nextTick(renderGantt)
})

// ── Helpers ────────────────────────────────────────────────────────────────
const PRIORITY_COLORS: Record<string, string> = {
  low: '#10B981', medium: '#3B82F6', high: '#F59E0B', urgent: '#EF4444',
}
const PRIORITY_LABELS: Record<string, string> = {
  low: 'Low', medium: 'Medium', high: 'High', urgent: 'Urgent',
}
function priorityColor(p: string) { return PRIORITY_COLORS[p] ?? '#6B7280' }
function formatDate(iso: string | null) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' })
}
function isOverdue(iso: string | null) {
  if (!iso) return false
  return new Date(iso) < new Date()
}

onMounted(fetchProject)
</script>

<template>
  <div class="flex flex-col h-screen bg-[#FFFDF5] overflow-hidden">
    <!-- ── Top Bar ─────────────────────────────────────────────────────────── -->
    <div class="flex-none bg-black text-white px-4 py-3 flex items-center gap-3 border-b-4 border-yellow-400">
      <NuxtLink to="/tools/project" class="flex items-center gap-1 text-yellow-400 hover:text-white font-bold text-sm uppercase">
        <Icon name="heroicons:arrow-left" class="w-4 h-4" />
        Projects
      </NuxtLink>
      <span class="text-gray-600">|</span>
      <h1 class="font-black text-lg truncate flex-1">{{ project?.name ?? 'Loading...' }}</h1>

      <!-- View switcher -->
      <div class="flex items-center gap-1 border-2 border-yellow-400 p-0.5">
        <button
          @click="activeView = 'board'"
          :class="activeView === 'board' ? 'bg-yellow-400 text-black' : 'text-yellow-400 hover:bg-yellow-400/20'"
          class="px-3 py-1 font-black text-xs uppercase transition-colors"
        >Board</button>
        <button
          @click="activeView = 'gantt'"
          :class="activeView === 'gantt' ? 'bg-yellow-400 text-black' : 'text-yellow-400 hover:bg-yellow-400/20'"
          class="px-3 py-1 font-black text-xs uppercase transition-colors"
        >Gantt</button>
      </div>

      <button
        @click="showMembers = true"
        class="flex items-center gap-1 px-3 py-1.5 border-2 border-yellow-400 text-yellow-400 hover:bg-yellow-400 hover:text-black font-bold text-xs uppercase transition-colors"
      >
        <Icon name="heroicons:users" class="w-4 h-4" />
        Members
      </button>
      <button
        v-if="isOwner"
        @click="showSettings = true; Object.assign(settingsForm, { name: project!.name, description: project!.description, is_public: project!.is_public })"
        class="flex items-center gap-1 px-3 py-1.5 border-2 border-yellow-400 text-yellow-400 hover:bg-yellow-400 hover:text-black font-bold text-xs uppercase transition-colors"
      >
        <Icon name="heroicons:cog-6-tooth" class="w-4 h-4" />
      </button>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="flex-1 flex items-center justify-center text-gray-500 font-bold">Loading project...</div>
    <div v-else-if="error" class="flex-1 flex items-center justify-center text-red-600 font-bold">{{ error }}</div>

    <!-- ── Board View ──────────────────────────────────────────────────────── -->
    <div v-else-if="activeView === 'board'" class="flex-1 overflow-x-auto overflow-y-hidden p-4">
      <div class="flex gap-4 h-full" style="min-width: max-content">
        <!-- Columns -->
        <div
          v-for="col in project!.columns"
          :key="col.id"
          class="flex flex-col w-72 flex-none"
          @dragover="onDragOver($event, col.id)"
          @dragleave="onDragLeave"
          @drop="onDrop($event, col)"
        >
          <!-- Column header -->
          <div
            class="flex items-center justify-between px-3 py-2 border-4 border-black font-black text-sm uppercase mb-2"
            :style="{ backgroundColor: col.color + '33', borderLeftColor: col.color }"
          >
            <span class="flex items-center gap-2">
              <span class="w-3 h-3 rounded-full border-2 border-black" :style="{ backgroundColor: col.color }"></span>
              {{ col.name }}
              <span class="text-xs bg-black text-white px-1.5 py-0.5 font-black">{{ col.tasks.length }}</span>
            </span>
            <div class="flex items-center gap-1">
              <button
                v-if="isEditor"
                @click="openCreateTask(col)"
                class="text-black hover:text-blue-600 transition-colors"
                title="Add task"
              >
                <Icon name="heroicons:plus" class="w-4 h-4" />
              </button>
              <button
                v-if="isOwner"
                @click="deleteColumn(col)"
                class="text-black hover:text-red-600 transition-colors"
                title="Delete column"
              >
                <Icon name="heroicons:trash" class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <!-- Task list -->
          <div
            class="flex-1 overflow-y-auto space-y-2 pr-0.5 pb-2 min-h-[60px] transition-colors"
            :class="dragOverCol === col.id ? 'bg-blue-50 border-2 border-dashed border-blue-400' : ''"
          >
            <div
              v-for="task in col.tasks"
              :key="task.id"
              draggable="true"
              @dragstart="onDragStart(task, col.id)"
              class="bg-white border-4 border-black shadow-[3px_3px_0_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_#000] transition-all cursor-pointer"
              @click="openDetail(task)"
            >
              <!-- Color bar -->
              <div class="h-1.5" :style="{ backgroundColor: task.color }"></div>
              <div class="p-3">
                <p class="font-bold text-sm text-black leading-snug mb-2">{{ task.title }}</p>
                <div class="flex items-center justify-between flex-wrap gap-1">
                  <span
                    class="text-xs font-black px-2 py-0.5 border-2 border-black"
                    :style="{ backgroundColor: priorityColor(task.priority) + '33', color: priorityColor(task.priority) }"
                  >{{ PRIORITY_LABELS[task.priority] }}</span>
                  <span v-if="task.due_date" :class="isOverdue(task.due_date) ? 'text-red-600' : 'text-gray-500'" class="text-xs font-bold flex items-center gap-1">
                    <Icon name="heroicons:calendar" class="w-3 h-3" />
                    {{ formatDate(task.due_date) }}
                  </span>
                </div>
                <div v-if="task.assignee_email || task.comment_count > 0" class="flex items-center justify-between mt-2">
                  <span v-if="task.assignee_email" class="text-xs text-gray-500 truncate max-w-[120px]">
                    <Icon name="heroicons:user" class="w-3 h-3 inline" /> {{ task.assignee_email.split('@')[0] }}
                  </span>
                  <span v-if="task.comment_count > 0" class="text-xs text-gray-400 flex items-center gap-1 ml-auto">
                    <Icon name="heroicons:chat-bubble-left" class="w-3 h-3" /> {{ task.comment_count }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Empty state -->
            <div
              v-if="col.tasks.length === 0"
              class="text-center py-6 text-gray-400 text-xs font-bold uppercase"
            >Empty</div>
          </div>

          <!-- Add task button -->
          <button
            v-if="isEditor"
            @click="openCreateTask(col)"
            class="mt-2 w-full py-2 border-4 border-dashed border-gray-400 text-gray-500 font-bold text-sm hover:border-black hover:text-black uppercase transition-colors flex items-center justify-center gap-1"
          >
            <Icon name="heroicons:plus" class="w-4 h-4" />
            Add Task
          </button>
        </div>

        <!-- Add Column button -->
        <div v-if="isOwner" class="w-64 flex-none">
          <button
            @click="addColModal = true"
            class="w-full py-3 border-4 border-dashed border-gray-400 text-gray-500 font-bold text-sm hover:border-black hover:text-black uppercase transition-colors flex items-center justify-center gap-2"
          >
            <Icon name="heroicons:plus" class="w-4 h-4" />
            Add Column
          </button>
        </div>
      </div>
    </div>

    <!-- ── Gantt View ──────────────────────────────────────────────────────── -->
    <div v-else-if="activeView === 'gantt'" class="flex-1 overflow-auto p-4">
      <div class="mb-4 text-sm text-gray-500 font-bold">
        Tasks with <strong>Start Date</strong> and <strong>Due Date</strong> will appear on the Gantt chart. Click a task bar to view details.
      </div>
      <div ref="ganttEl" class="gantt-wrapper min-h-[300px]"></div>
    </div>

    <!-- ── Task Detail Panel ───────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="detailTask"
        class="fixed inset-0 bg-black/50 z-50 flex justify-end"
        @click.self="detailTask = null"
      >
        <div class="w-full max-w-lg bg-white border-l-4 border-black flex flex-col h-full">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b-4 border-black bg-gray-50">
            <h2 class="font-black text-xl flex-1 mr-4">{{ detailTask.title }}</h2>
            <div class="flex items-center gap-2">
              <button
                v-if="isEditor"
                @click="openEditTask(detailTask); detailTask = null"
                class="p-2 border-2 border-black hover:bg-yellow-300 transition-colors"
                title="Edit task"
              >
                <Icon name="heroicons:pencil" class="w-4 h-4" />
              </button>
              <button
                v-if="isEditor"
                @click="deleteTask(detailTask)"
                class="p-2 border-2 border-black hover:bg-red-300 transition-colors"
                title="Delete task"
              >
                <Icon name="heroicons:trash" class="w-4 h-4" />
              </button>
              <button @click="detailTask = null" class="p-2 border-2 border-black hover:bg-gray-200 transition-colors">
                <Icon name="heroicons:x-mark" class="w-4 h-4" />
              </button>
            </div>
          </div>
          <div class="flex-1 overflow-y-auto p-6 space-y-5">
            <!-- Meta -->
            <div class="grid grid-cols-2 gap-3 text-sm">
              <div class="border-2 border-black p-3">
                <div class="text-xs font-black uppercase text-gray-500 mb-1">Priority</div>
                <span class="font-black" :style="{ color: priorityColor(detailTask.priority) }">{{ PRIORITY_LABELS[detailTask.priority] }}</span>
              </div>
              <div class="border-2 border-black p-3">
                <div class="text-xs font-black uppercase text-gray-500 mb-1">Column</div>
                <span class="font-bold">{{ project!.columns.find(c => c.id === detailTask!.column_id)?.name }}</span>
              </div>
              <div v-if="detailTask.assignee_email" class="border-2 border-black p-3">
                <div class="text-xs font-black uppercase text-gray-500 mb-1">Assignee</div>
                <span class="font-bold truncate">{{ detailTask.assignee_email }}</span>
              </div>
              <div v-if="detailTask.due_date" class="border-2 border-black p-3">
                <div class="text-xs font-black uppercase text-gray-500 mb-1">Due Date</div>
                <span class="font-bold" :class="isOverdue(detailTask.due_date) ? 'text-red-600' : ''">{{ formatDate(detailTask.due_date) }}</span>
              </div>
              <div v-if="detailTask.start_date" class="border-2 border-black p-3">
                <div class="text-xs font-black uppercase text-gray-500 mb-1">Start Date</div>
                <span class="font-bold">{{ formatDate(detailTask.start_date) }}</span>
              </div>
            </div>

            <!-- Description -->
            <div v-if="detailTask.description">
              <div class="text-xs font-black uppercase text-gray-500 mb-2">Description</div>
              <p class="text-sm text-gray-700 whitespace-pre-wrap border-l-4 border-gray-300 pl-3">{{ detailTask.description }}</p>
            </div>

            <!-- Comments -->
            <div>
              <div class="text-xs font-black uppercase text-gray-500 mb-3 flex items-center gap-2">
                Comments
                <span class="bg-black text-white text-xs px-1.5 py-0.5 font-black">{{ comments.length }}</span>
              </div>
              <div class="space-y-3 mb-4 max-h-60 overflow-y-auto">
                <div v-for="c in comments" :key="c.id" class="border-2 border-black p-3">
                  <div class="flex items-center justify-between mb-1">
                    <span class="text-xs font-black text-gray-700">{{ c.author_email.split('@')[0] }}</span>
                    <div class="flex items-center gap-2">
                      <span class="text-xs text-gray-400">{{ formatDate(c.created_at) }}</span>
                      <button
                        v-if="c.author_email === currentUser?.email"
                        @click="deleteComment(c)"
                        class="text-gray-400 hover:text-red-600"
                      >
                        <Icon name="heroicons:trash" class="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                  <p class="text-sm text-gray-800 whitespace-pre-wrap">{{ c.body }}</p>
                </div>
                <div v-if="comments.length === 0" class="text-center text-xs text-gray-400 py-4 uppercase font-bold">No comments yet</div>
              </div>
              <div v-if="isEditor" class="flex gap-2">
                <textarea
                  v-model="newComment"
                  rows="2"
                  placeholder="Write a comment..."
                  class="flex-1 border-4 border-black px-3 py-2 text-sm font-bold focus:outline-none focus:bg-yellow-50 resize-none"
                  @keydown.ctrl.enter="postComment"
                />
                <button
                  @click="postComment"
                  :disabled="postingComment || !newComment.trim()"
                  class="px-4 bg-black text-white font-black uppercase text-xs border-4 border-black disabled:opacity-50"
                >Send</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Task Create/Edit Modal ─────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="taskModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="taskModal = false"
      >
        <div class="bg-white border-4 border-black shadow-[8px_8px_0_#000] w-full max-w-lg max-h-[90vh] flex flex-col">
          <div class="bg-black text-white px-6 py-4 flex items-center justify-between flex-none">
            <h2 class="font-black uppercase text-lg">{{ editingTask ? 'Edit Task' : `Add Task — ${taskColumn?.name}` }}</h2>
            <button @click="taskModal = false"><Icon name="heroicons:x-mark" class="w-6 h-6" /></button>
          </div>
          <div class="p-6 space-y-4 overflow-y-auto flex-1">
            <div>
              <label class="block text-xs font-black uppercase mb-1">Title *</label>
              <input
                v-model="taskForm.title"
                type="text"
                class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none focus:bg-yellow-50"
                placeholder="Task title"
              />
            </div>
            <div>
              <label class="block text-xs font-black uppercase mb-1">Description</label>
              <textarea
                v-model="taskForm.description"
                rows="3"
                class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none focus:bg-yellow-50 resize-none text-sm"
                placeholder="Details..."
              />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-black uppercase mb-1">Priority</label>
                <select
                  v-model="taskForm.priority"
                  class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none bg-white"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
              <div>
                <label class="block text-xs font-black uppercase mb-1">Card Color</label>
                <div class="flex items-center gap-2 border-4 border-black px-3 py-1.5">
                  <input v-model="taskForm.color" type="color" class="w-8 h-8 border-2 border-black cursor-pointer" />
                  <span class="font-bold text-sm">{{ taskForm.color }}</span>
                </div>
              </div>
              <div>
                <label class="block text-xs font-black uppercase mb-1">Start Date</label>
                <input
                  v-model="taskForm.start_date"
                  type="date"
                  class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none"
                />
              </div>
              <div>
                <label class="block text-xs font-black uppercase mb-1">Due Date</label>
                <input
                  v-model="taskForm.due_date"
                  type="date"
                  class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none"
                />
              </div>
            </div>
            <div>
              <label class="block text-xs font-black uppercase mb-1">Assignee Email</label>
              <input
                v-model="taskForm.assignee_email"
                type="email"
                class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none focus:bg-yellow-50"
                placeholder="user@example.com"
              />
            </div>
          </div>
          <div class="px-6 pb-6 flex gap-3 flex-none">
            <button @click="taskModal = false" class="flex-1 py-3 border-4 border-black font-black uppercase hover:bg-gray-100">Cancel</button>
            <button
              @click="saveTask"
              :disabled="savingTask || !taskForm.title.trim()"
              class="flex-1 py-3 bg-black text-white font-black uppercase border-4 border-black disabled:opacity-50"
            >{{ savingTask ? 'Saving...' : (editingTask ? 'Update' : 'Create') }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Add Column Modal ───────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="addColModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="addColModal = false"
      >
        <div class="bg-white border-4 border-black shadow-[8px_8px_0_#000] w-full max-w-sm">
          <div class="bg-black text-white px-6 py-4 flex items-center justify-between">
            <h2 class="font-black uppercase">New Column</h2>
            <button @click="addColModal = false"><Icon name="heroicons:x-mark" class="w-6 h-6" /></button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-xs font-black uppercase mb-1">Column Name *</label>
              <input
                v-model="newColName"
                type="text"
                class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none focus:bg-yellow-50"
                @keydown.enter="addColumn"
              />
            </div>
            <div>
              <label class="block text-xs font-black uppercase mb-1">Color</label>
              <div class="flex items-center gap-2 border-4 border-black px-3 py-1.5">
                <input v-model="newColColor" type="color" class="w-8 h-8 border-2 border-black cursor-pointer" />
                <span class="font-bold text-sm">{{ newColColor }}</span>
              </div>
            </div>
          </div>
          <div class="px-6 pb-6 flex gap-3">
            <button @click="addColModal = false" class="flex-1 py-3 border-4 border-black font-black uppercase hover:bg-gray-100">Cancel</button>
            <button
              @click="addColumn"
              :disabled="addingCol || !newColName.trim()"
              class="flex-1 py-3 bg-black text-white font-black uppercase border-4 border-black disabled:opacity-50"
            >{{ addingCol ? 'Adding...' : 'Add' }}</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Members Panel ──────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="showMembers"
        class="fixed inset-0 bg-black/50 z-50 flex justify-end"
        @click.self="showMembers = false"
      >
        <div class="w-full max-w-sm bg-white border-l-4 border-black flex flex-col h-full">
          <div class="flex items-center justify-between px-6 py-4 border-b-4 border-black bg-black text-white">
            <h2 class="font-black uppercase text-lg">Members</h2>
            <button @click="showMembers = false"><Icon name="heroicons:x-mark" class="w-6 h-6" /></button>
          </div>
          <div class="flex-1 overflow-y-auto p-6 space-y-3">
            <div
              v-for="m in project!.members"
              :key="m.email"
              class="flex items-center justify-between border-2 border-black p-3"
            >
              <div>
                <p class="font-bold text-sm">{{ m.email }}</p>
                <p class="text-xs font-black uppercase" :class="m.role === 'owner' ? 'text-yellow-600' : m.role === 'editor' ? 'text-blue-600' : 'text-gray-500'">
                  {{ m.role }}
                </p>
              </div>
              <button
                v-if="isOwner && m.role !== 'owner'"
                @click="removeMember(m.email)"
                class="text-gray-400 hover:text-red-600 transition-colors"
              >
                <Icon name="heroicons:x-mark" class="w-4 h-4" />
              </button>
            </div>
          </div>
          <div v-if="isOwner" class="border-t-4 border-black p-6 space-y-3">
            <p class="text-xs font-black uppercase text-gray-500">Invite Member</p>
            <input
              v-model="inviteEmail"
              type="email"
              placeholder="email@example.com"
              class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none focus:bg-yellow-50 text-sm"
            />
            <div class="flex gap-2">
              <select v-model="inviteRole" class="flex-1 border-4 border-black px-2 py-2 font-bold bg-white text-sm">
                <option value="editor">Editor</option>
                <option value="viewer">Viewer</option>
              </select>
              <button
                @click="inviteMember"
                :disabled="inviting || !inviteEmail.trim()"
                class="px-4 py-2 bg-black text-white font-black uppercase text-xs border-4 border-black disabled:opacity-50"
              >{{ inviting ? '...' : 'Invite' }}</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ── Settings Modal ────────────────────────────────────────────────── -->
    <Teleport to="body">
      <div
        v-if="showSettings"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="showSettings = false"
      >
        <div class="bg-white border-4 border-black shadow-[8px_8px_0_#000] w-full max-w-md">
          <div class="bg-black text-white px-6 py-4 flex items-center justify-between">
            <h2 class="font-black uppercase text-lg">Project Settings</h2>
            <button @click="showSettings = false"><Icon name="heroicons:x-mark" class="w-6 h-6" /></button>
          </div>
          <div class="p-6 space-y-4">
            <div>
              <label class="block text-xs font-black uppercase mb-1">Project Name *</label>
              <input
                v-model="settingsForm.name"
                type="text"
                class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none focus:bg-yellow-50"
              />
            </div>
            <div>
              <label class="block text-xs font-black uppercase mb-1">Description</label>
              <textarea
                v-model="settingsForm.description"
                rows="3"
                class="w-full border-4 border-black px-3 py-2 font-bold focus:outline-none focus:bg-yellow-50 resize-none text-sm"
              />
            </div>
            <label class="flex items-center gap-3 cursor-pointer select-none">
              <input v-model="settingsForm.is_public" type="checkbox" class="w-5 h-5 border-4 border-black accent-black" />
              <span class="font-bold text-sm">Public (anyone can view)</span>
            </label>
          </div>
          <div class="px-6 pb-6 flex gap-3">
            <button @click="showSettings = false" class="flex-1 py-3 border-4 border-black font-black uppercase hover:bg-gray-100">Cancel</button>
            <button
              @click="saveSettings"
              :disabled="savingSettings || !settingsForm.name.trim()"
              class="flex-1 py-3 bg-black text-white font-black uppercase border-4 border-black disabled:opacity-50"
            >{{ savingSettings ? 'Saving...' : 'Save' }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style>
/* Frappe Gantt overrides */
.gantt-wrapper .gantt .bar {
  fill: #3B82F6;
}
.gantt-wrapper .gantt .bar-label {
  font-weight: 700;
  font-size: 11px;
}
.gantt-wrapper svg {
  border: 4px solid #000;
}
</style>
