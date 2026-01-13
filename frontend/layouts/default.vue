<template>
  <div class="min-h-screen bg-[var(--background)]">
    <!-- Editorial Header -->
    <header class="bg-[var(--background)] border-b-2 border-[var(--foreground)]">
      <div class="max-w-6xl mx-auto px-6 md:px-8 lg:px-12">
        <div class="flex justify-between items-center h-16">
          <!-- Logo -->
          <NuxtLink to="/dashboard" class="flex items-center space-x-3 no-underline">
            <div class="w-10 h-10 flex items-center justify-center border-2 border-[var(--foreground)] rounded-md">
              <Icon name="heroicons:hand-thumb-up-solid" class="w-5 h-5 text-[var(--foreground)]" />
            </div>
            <span class="font-serif font-bold text-xl tracking-tight">ManTul</span>
          </NuxtLink>
          
          <!-- Navigation -->
          <nav class="flex items-center space-x-6">
            <NuxtLink 
              to="/dashboard" 
              class="flex items-center space-x-2 text-sm uppercase tracking-widest text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors duration-100 no-underline"
            >
              <Icon name="heroicons:squares-2x2" class="w-4 h-4" />
              <span class="hidden sm:inline">Tools</span>
            </NuxtLink>
            
            <NuxtLink 
              to="/settings" 
              class="flex items-center space-x-2 text-sm uppercase tracking-widest text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors duration-100 no-underline"
            >
              <Icon name="heroicons:cog-6-tooth" class="w-4 h-4" />
              <span class="hidden sm:inline">Settings</span>
            </NuxtLink>
            
            <!-- User Info & Logout -->
            <div class="flex items-center space-x-3 border-l border-[var(--border)] pl-6">
              <div v-if="currentUser" class="hidden md:block text-right">
                <p class="text-sm font-bold leading-tight">{{ currentUser.name }}</p>
                <p class="text-xs text-[var(--muted-foreground)]">{{ currentUser.nip || currentUser.email }}</p>
              </div>
              <button 
                @click="logout" 
                class="flex items-center space-x-2 text-sm uppercase tracking-widest text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors duration-100"
              >
                <span>Logout</span>
                <Icon name="heroicons:arrow-right-on-rectangle" class="w-4 h-4" />
              </button>
            </div>
          </nav>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-6xl mx-auto py-12 px-6 md:px-8 lg:px-12">
      <slot />
    </main>

    <!-- Footer -->
    <footer class="border-t border-[var(--border-light)] py-6">
      <div class="max-w-6xl mx-auto px-6 md:px-8 lg:px-12">
        <p class="text-xs text-[var(--muted-foreground)] text-center font-mono tracking-wide">
          ManTul — DIGITAL PRODUCTIVITY SUITE
        </p>
        <p class="text-xs text-[var(--muted-foreground)] text-center mt-2 opacity-70">
          Crafted by I.A. — IT LMAN
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
// Get current user from cookies
const tokenCookie = useCookie('ocr_token')
const userCookie = useCookie('ocr_user')

const currentUser = computed(() => {
  if (!userCookie.value) return null
  try {
    if (typeof userCookie.value === 'string') {
      return JSON.parse(userCookie.value)
    }
    return userCookie.value
  } catch {
    return null
  }
})

const logout = () => {
  tokenCookie.value = null
  userCookie.value = null
  navigateTo('/login')
}
</script>


