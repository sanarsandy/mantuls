<template>
  <div class="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <!-- Header -->
    <div class="mb-12 pb-8 border-b-4 border-[var(--foreground)]">
      <NuxtLink to="/dashboard" class="text-[var(--muted-foreground)] hover:text-[var(--foreground)] flex items-center mb-4 text-sm transition-colors">
        <Icon name="heroicons:arrow-left" class="w-4 h-4 mr-1" />
        Back to Tools
      </NuxtLink>
      <h1 class="font-serif text-4xl md:text-5xl font-bold tracking-tighter">
        PANDUAN
      </h1>
      <p class="text-[var(--muted-foreground)] mt-2 text-lg">
        Panduan lengkap penggunaan semua tools di ManTuls
      </p>
    </div>

    <!-- Quick Navigation -->
    <div class="card-mono p-6">
      <h2 class="font-bold font-serif text-xl mb-4">Daftar Tools</h2>
      <div class="flex flex-wrap gap-2">
        <a v-for="tool in tools" :key="tool.id" 
           :href="`#${tool.id}`"
           class="px-3 py-1 text-sm border border-[var(--border)] hover:bg-[var(--accent)] transition-colors">
          {{ tool.name }}
        </a>
      </div>
    </div>

    <!-- Tool Guides -->
    <div class="space-y-8">
      <div v-for="tool in tools" :key="tool.id" :id="tool.id" class="card-mono p-8 scroll-mt-8">
        <div class="flex items-start gap-4 mb-6">
          <div class="w-14 h-14 border-2 border-[var(--foreground)] flex items-center justify-center flex-shrink-0">
            <Icon :name="tool.icon" class="w-7 h-7" />
          </div>
          <div>
            <h2 class="font-serif text-2xl font-bold">{{ tool.name }}</h2>
            <p class="text-[var(--muted-foreground)] mt-1">{{ tool.description }}</p>
          </div>
        </div>

        <!-- Supported Formats -->
        <div class="mb-6">
          <h3 class="font-bold text-sm uppercase tracking-wider mb-2 text-[var(--muted-foreground)]">Format yang Didukung</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="format in tool.formats" :key="format" 
                  class="px-2 py-1 text-xs font-mono bg-[var(--accent)] text-[var(--background)]">
              {{ format }}
            </span>
          </div>
        </div>

        <!-- How to Use -->
        <div class="mb-6">
          <h3 class="font-bold text-sm uppercase tracking-wider mb-3 text-[var(--muted-foreground)]">Cara Penggunaan</h3>
          <ol class="space-y-2">
            <li v-for="(step, index) in tool.steps" :key="index" class="flex items-start gap-3">
              <span class="w-6 h-6 bg-[var(--foreground)] text-[var(--background)] flex items-center justify-center text-xs font-bold flex-shrink-0">
                {{ index + 1 }}
              </span>
              <span class="text-sm">{{ step }}</span>
            </li>
          </ol>
        </div>

        <!-- Tips -->
        <div v-if="tool.tips && tool.tips.length" class="bg-[var(--muted)]/10 p-4 border-l-4 border-[var(--foreground)]">
          <h3 class="font-bold text-sm mb-2">💡 Tips</h3>
          <ul class="space-y-1 text-sm text-[var(--muted-foreground)]">
            <li v-for="(tip, index) in tool.tips" :key="index">• {{ tip }}</li>
          </ul>
        </div>

        <!-- CTA Button -->
        <NuxtLink :to="tool.link" class="btn-mono-primary inline-flex items-center mt-6">
          <Icon name="heroicons:arrow-right" class="w-4 h-4 mr-2" />
          Gunakan {{ tool.name }}
        </NuxtLink>
      </div>
    </div>

    <!-- Back to Top -->
    <div class="text-center py-8">
      <a href="#" class="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors">
        ↑ Kembali ke atas
      </a>
    </div>
  </div>
</template>

<script setup>
definePageMeta({
  middleware: ['auth']
})

useHead({
  title: 'Panduan Tools — ManTuls'
})

const tools = [
  {
    id: 'ocr',
    name: 'OCR Scanner',
    icon: 'heroicons:document-magnifying-glass',
    description: 'Ekstrak teks dari gambar atau dokumen PDF menggunakan teknologi AI.',
    formats: ['JPG', 'PNG', 'PDF'],
    steps: [
      'Upload file gambar atau PDF yang ingin diekstrak teksnya.',
      'Pilih provider OCR jika diperlukan (default: PaddleOCR).',
      'Tunggu proses ekstraksi selesai.',
      'Salin atau download hasil teks yang diekstrak.'
    ],
    tips: [
      'Gunakan gambar dengan resolusi tinggi untuk hasil lebih akurat.',
      'Pastikan teks dalam gambar jelas dan tidak blur.',
      'PDF multi-halaman akan diproses secara paralel untuk kecepatan maksimal.'
    ],
    link: '/tools/ocr'
  },
  {
    id: 'merge-pdf',
    name: 'Merge PDF',
    icon: 'heroicons:document-duplicate',
    description: 'Gabungkan beberapa file PDF menjadi satu dokumen.',
    formats: ['PDF'],
    steps: [
      'Upload minimal 2 file PDF yang ingin digabung.',
      'Atur urutan file dengan drag & drop jika diperlukan.',
      'Klik tombol "Merge" untuk menggabungkan.',
      'Download file PDF hasil penggabungan.'
    ],
    tips: [
      'Urutan file menentukan urutan halaman di PDF hasil.',
      'Tidak ada batas jumlah file yang bisa digabung.'
    ],
    link: '/tools/merge-pdf'
  },
  {
    id: 'split-pdf',
    name: 'Split PDF',
    icon: 'heroicons:scissors',
    description: 'Pisahkan file PDF menjadi halaman-halaman terpisah.',
    formats: ['PDF'],
    steps: [
      'Upload file PDF yang ingin dipisah.',
      'Pilih mode: pisah semua halaman atau pilih range tertentu.',
      'Klik tombol "Split" untuk memproses.',
      'Download file ZIP berisi halaman terpisah atau PDF dengan halaman terpilih.'
    ],
    tips: [
      'Mode "All" akan memisah setiap halaman menjadi file terpisah.',
      'Gunakan format range seperti "1-3, 5, 7-10" untuk memilih halaman spesifik.'
    ],
    link: '/tools/split-pdf'
  },
  {
    id: 'compress-pdf',
    name: 'Compress PDF',
    icon: 'heroicons:archive-box-arrow-down',
    description: 'Kompres ukuran file PDF tanpa mengurangi kualitas secara signifikan.',
    formats: ['PDF'],
    steps: [
      'Upload file PDF yang ingin dikompres.',
      'Pilih level kompresi: Low, Medium, atau High.',
      'Klik tombol "Compress" untuk memproses.',
      'Download file PDF yang sudah dikompres.'
    ],
    tips: [
      'Level "Medium" biasanya memberikan keseimbangan terbaik antara ukuran dan kualitas.',
      'File dengan banyak gambar akan mendapat kompresi lebih signifikan.'
    ],
    link: '/tools/compress-pdf'
  },
  {
    id: 'pdf-to-word',
    name: 'PDF to Word',
    icon: 'heroicons:document-arrow-down',
    description: 'Konversi file PDF menjadi dokumen Word yang bisa diedit.',
    formats: ['PDF → DOCX'],
    steps: [
      'Upload file PDF yang ingin dikonversi.',
      'Klik tombol "Convert to Word".',
      'Tunggu proses konversi selesai.',
      'Download file DOCX hasil konversi.'
    ],
    tips: [
      'Paling baik untuk PDF dengan teks (bukan hasil scan).',
      'Untuk PDF hasil scan, gunakan OCR terlebih dahulu.',
      'Formatting mungkin sedikit berbeda tergantung kompleksitas PDF.'
    ],
    link: '/tools/pdf-to-word'
  },
  {
    id: 'word-to-pdf',
    name: 'Word to PDF',
    icon: 'heroicons:document-arrow-up',
    description: 'Konversi dokumen Word menjadi file PDF.',
    formats: ['DOC', 'DOCX → PDF'],
    steps: [
      'Upload file Word (DOC/DOCX).',
      'Klik tombol "Convert to PDF".',
      'Tunggu proses konversi selesai.',
      'Download file PDF hasil konversi.'
    ],
    tips: [
      'Formatting, font, dan layout akan dipertahankan.',
      'Cocok untuk membuat dokumen yang mudah dibagikan.'
    ],
    link: '/tools/word-to-pdf'
  },
  {
    id: 'watermark-pdf',
    name: 'Watermark PDF',
    icon: 'heroicons:paint-brush',
    description: 'Tambahkan watermark teks ke semua halaman PDF.',
    formats: ['PDF'],
    steps: [
      'Upload file PDF.',
      'Masukkan teks watermark (contoh: CONFIDENTIAL, DRAFT).',
      'Pilih posisi (diagonal/center) dan transparansi.',
      'Klik "Apply Watermark" dan download hasilnya.'
    ],
    tips: [
      'Gunakan watermark "DRAFT" untuk dokumen yang belum final.',
      'Transparansi 30% biasanya sudah cukup terlihat tanpa mengganggu konten.'
    ],
    link: '/tools/watermark-pdf'
  },
  {
    id: 'protect-pdf',
    name: 'Protect PDF',
    icon: 'heroicons:lock-closed',
    description: 'Enkripsi PDF dengan password untuk keamanan.',
    formats: ['PDF'],
    steps: [
      'Upload file PDF yang ingin diproteksi.',
      'Masukkan password yang diinginkan.',
      'Klik "Protect" untuk mengenkripsi.',
      'Download PDF yang sudah terproteksi.'
    ],
    tips: [
      'Gunakan password yang kuat (kombinasi huruf, angka, simbol).',
      'Simpan password di tempat aman - tidak bisa dipulihkan jika lupa.'
    ],
    link: '/tools/protect-pdf'
  },
  {
    id: 'unlock-pdf',
    name: 'Unlock PDF',
    icon: 'heroicons:lock-open',
    description: 'Hapus password dari PDF yang terenkripsi.',
    formats: ['PDF (encrypted)'],
    steps: [
      'Upload file PDF yang terproteksi.',
      'Masukkan password PDF tersebut.',
      'Klik "Unlock" untuk mendekripsi.',
      'Download PDF yang sudah tidak terproteksi.'
    ],
    tips: [
      'Anda harus mengetahui password asli untuk membuka PDF.',
      'Tool ini tidak bisa membobol password yang tidak diketahui.'
    ],
    link: '/tools/unlock-pdf'
  },
  {
    id: 'image-converter',
    name: 'Image Converter',
    icon: 'heroicons:photo',
    description: 'Konversi format gambar antara JPG, PNG, dan WebP.',
    formats: ['JPG', 'PNG', 'WEBP'],
    steps: [
      'Upload gambar yang ingin dikonversi.',
      'Pilih format output yang diinginkan.',
      'Atur kualitas jika diperlukan (untuk format lossy).',
      'Download gambar hasil konversi.'
    ],
    tips: [
      'PNG terbaik untuk gambar dengan transparansi.',
      'WebP memberikan ukuran file terkecil dengan kualitas baik.',
      'JPG cocok untuk foto dengan warna banyak.'
    ],
    link: '/tools/image-converter'
  },
  {
    id: 'remove-bg',
    name: 'Remove Background',
    icon: 'heroicons:sparkles',
    description: 'Hapus background gambar secara otomatis menggunakan AI.',
    formats: ['JPG', 'PNG', 'WEBP → PNG'],
    steps: [
      'Upload gambar dengan objek yang jelas.',
      'Tunggu AI memproses penghapusan background.',
      'Lihat preview hasil dengan background transparan.',
      'Download gambar PNG dengan transparansi.'
    ],
    tips: [
      'Paling baik untuk foto produk, portrait, atau objek dengan kontras jelas.',
      'Proses pertama mungkin sedikit lambat karena model AI perlu dimuat.',
      'Hasil selalu dalam format PNG untuk mendukung transparansi.'
    ],
    link: '/tools/remove-bg'
  },
  {
    id: 'qr-generator',
    name: 'QR Code Generator',
    icon: 'heroicons:qr-code',
    description: 'Buat QR code untuk link, teks, atau data lainnya.',
    formats: ['PNG'],
    steps: [
      'Masukkan URL, teks, atau data yang ingin dijadikan QR code.',
      'Atur ukuran QR code jika diperlukan.',
      'Klik "Generate" untuk membuat QR code.',
      'Download gambar PNG QR code.'
    ],
    tips: [
      'URL yang lebih pendek menghasilkan QR code yang lebih mudah dipindai.',
      'Coba scan QR code sebelum menyebarluaskan untuk memastikan berfungsi.'
    ],
    link: '/tools/qr-generator'
  }
]
</script>
