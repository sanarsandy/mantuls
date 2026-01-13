<template>
  <div class="min-h-screen bg-[var(--background)] flex items-center justify-center px-6 py-12 relative overflow-hidden">
    <!-- Decorative Background Pattern -->
    <div class="absolute inset-0 opacity-5 pointer-events-none" 
         style="background-image: radial-gradient(var(--foreground) 1px, transparent 1px); background-size: 24px 24px;">
    </div>

    <!-- Decorative Corner Elements -->
    <div class="absolute top-0 left-0 w-32 h-32 border-r-2 border-b-2 border-[var(--foreground)] opacity-20"></div>
    <div class="absolute bottom-0 right-0 w-32 h-32 border-l-2 border-t-2 border-[var(--foreground)] opacity-20"></div>

    <div class="w-full max-w-md relative z-10">
      
      <!-- Editorial Header -->
      <div class="text-center mb-10">
        <div class="inline-block p-4 border-2 border-[var(--foreground)] bg-[var(--background)] shadow-[4px_4px_0px_0px_var(--foreground)] mb-6 transform hover:-translate-y-1 transition-transform duration-300">
           <Icon name="heroicons:hand-thumb-up-solid" class="w-12 h-12 text-[var(--foreground)]" />
        </div>
        
        <h1 class="font-serif text-5xl md:text-6xl font-bold tracking-tighter leading-none mb-2">
          ManTul
        </h1>
        
        <!-- Subtitle with lines -->
        <div class="flex items-center justify-center gap-4 text-[var(--muted-foreground)]">
          <div class="h-[1px] w-8 bg-[var(--muted-foreground)]"></div>
          <h2 class="font-serif text-lg tracking-widest uppercase font-bold">LMAN Office Tools</h2>
          <div class="h-[1px] w-8 bg-[var(--muted-foreground)]"></div>
        </div>
      </div>

      <!-- Login Form Card -->
      <div class="border-2 border-[var(--foreground)] bg-[var(--background)] p-8 shadow-[8px_8px_0px_0px_var(--foreground)] relative">
        <!-- Card Decoration -->
        <div class="absolute top-4 right-4 flex space-x-1">
          <div class="w-2 h-2 rounded-full bg-[var(--foreground)]"></div>
          <div class="w-2 h-2 rounded-full border border-[var(--foreground)]"></div>
          <div class="w-2 h-2 rounded-full bg-[var(--foreground)] opacity-50"></div>
        </div>

        <div class="mb-8 border-b-2 border-[var(--border)] pb-4">
           <h3 class="font-bold text-xl font-serif">Identification</h3>
           <p class="text-sm text-[var(--muted-foreground)]">Please login SSO LMAN to continue</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-6">
          
          <!-- Email or NIP -->
          <div class="group">
            <label for="userInput" class="label-mono mb-2 block font-bold text-xs uppercase tracking-wider">Email atau NIP</label>
            <div class="relative items-center">
              <input
                id="userInput"
                v-model="userInput"
                type="text"
                required
                class="w-full p-3 bg-[var(--accent)] border-2 border-transparent focus:border-[var(--foreground)] focus:bg-[var(--background)] outline-none transition-all placeholder:text-[var(--muted-foreground)]/50 font-mono text-sm"
                placeholder="email@lman.id atau NIP"
              />
              <div class="absolute bottom-0 left-0 h-[2px] w-0 bg-[var(--foreground)] transition-all duration-300 group-hover:w-full"></div>
            </div>
          </div>
          
          <!-- Password -->
          <div class="group">
            <label for="password" class="label-mono mb-2 block font-bold text-xs uppercase tracking-wider">Password</label>
            <div class="relative">
              <input
                id="password"
                v-model="password"
                type="password"
                required
                class="w-full p-3 bg-[var(--accent)] border-2 border-transparent focus:border-[var(--foreground)] focus:bg-[var(--background)] outline-none transition-all placeholder:text-[var(--muted-foreground)]/50 font-mono text-sm"
                placeholder="••••••••"
              />
              <div class="absolute bottom-0 left-0 h-[2px] w-0 bg-[var(--foreground)] transition-all duration-300 group-hover:w-full"></div>
            </div>
          </div>
          
          <!-- Error Message -->
          <div v-if="error" class="bg-red-50 border-l-4 border-red-500 p-4 text-sm font-mono text-red-700 animate-in fade-in slide-in-from-top-2">
            <p class="flex items-center gap-2">
               <Icon name="heroicons:exclamation-triangle" class="w-4 h-4" />
               {{ error }}
            </p>
          </div>
          
          <!-- Submit Button -->
          <button 
            type="submit" 
            :disabled="loading" 
            class="w-full bg-[var(--foreground)] text-[var(--background)] py-4 px-6 font-bold uppercase tracking-wider hover:bg-[var(--foreground)]/90 active:translate-y-1 transition-all flex items-center justify-center gap-2 group relative overflow-hidden"
          >
            <span class="relative z-10 flex items-center gap-2">
              <span v-if="loading">Processing...</span>
              <span v-else>Access Dashboard</span>
              <Icon v-if="!loading" name="heroicons:arrow-right" class="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </span>
            <div v-if="loading" class="absolute inset-0 bg-white/20 animate-pulse"></div>
          </button>
        </form>
      </div>

      <!-- Footer -->
      <div class="mt-12 text-center space-y-2 relative">
         <div class="flex items-center justify-center gap-2 mb-4 opacity-50">
            <div class="w-1 h-1 bg-[var(--foreground)] rounded-full"></div>
            <div class="w-1 h-1 bg-[var(--foreground)] rounded-full"></div>
            <div class="w-1 h-1 bg-[var(--foreground)] rounded-full"></div>
         </div>
         <p class="text-[10px] font-mono uppercase tracking-[0.2em] text-[var(--muted-foreground)]">
             ManTul — Digital Productivity Suite
         </p>
         <p class="text-[10px] text-[var(--muted-foreground)] opacity-60 font-serif italic">
             Crafted by I.A. — IT LMAN
         </p>
      </div>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  layout: false,
})

useHead({
  title: 'Login — ManTuls'
})

const config = useRuntimeConfig()
const apiBase = config.public.apiBase || 'http://localhost:8000'

const userInput = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  loading.value = true
  error.value = ''

  try {
    const response = await fetch(`${apiBase}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user: userInput.value.trim(),
        password: password.value
      })
    })

    const data = await response.json()

    if (response.ok && data.success) {
      // Store JWT token in cookie
      const tokenCookie = useCookie('ocr_token', { 
        maxAge: 60 * 60 * 24, // 24 hours
        sameSite: 'lax'
      })
      tokenCookie.value = data.token
      
      // Store user data in separate cookie for display
      const userCookie = useCookie('ocr_user', { 
        maxAge: 60 * 60 * 24,
        sameSite: 'lax'
      })
      userCookie.value = JSON.stringify(data.user)
      
      navigateTo('/dashboard')
    } else {
      error.value = data.detail || 'Login gagal. Periksa email/NIP dan password Anda.'
    }
  } catch (err) {
    console.error('Login error:', err)
    error.value = 'Tidak dapat terhubung ke server. Silakan coba lagi.'
  } finally {
    loading.value = false
  }
}
</script>

