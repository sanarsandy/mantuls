/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
    "./error.vue",
  ],
  theme: {
    extend: {
      // Minimalist Monochrome Design System
      colors: {
        // Core palette - Pure black & white
        background: '#FFFFFF',
        foreground: '#000000',

        // Muted tones
        muted: '#F5F5F5',
        'muted-foreground': '#525252',

        // Borders
        border: '#000000',
        'border-light': '#E5E5E5',

        // Card
        card: '#FFFFFF',
        'card-foreground': '#000000',

        // Ring (focus)
        ring: '#000000',
      },
      fontFamily: {
        // Serif for headlines - Editorial drama
        serif: ['Playfair Display', 'Georgia', 'serif'],
        // Serif for body - High readability
        body: ['Source Serif 4', 'Georgia', 'serif'],
        // Mono for labels, metadata
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      fontSize: {
        // Dramatic type scale
        '8xl': ['8rem', { lineHeight: '1' }],
        '9xl': ['10rem', { lineHeight: '1' }],
      },
      letterSpacing: {
        'tightest': '-0.05em',
        'widest': '0.1em',
      },
      borderRadius: {
        // Sharp corners everywhere - non-negotiable
        'none': '0px',
        DEFAULT: '0px',
        'sm': '0px',
        'md': '0px',
        'lg': '0px',
        'xl': '0px',
        '2xl': '0px',
        '3xl': '0px',
        'full': '0px',
      },
      borderWidth: {
        'hairline': '1px',
        '3': '3px',
        '4': '4px',
        '8': '8px',
      },
      boxShadow: {
        // No shadows - flat design with borders
        'none': 'none',
        DEFAULT: 'none',
        'sm': 'none',
        'md': 'none',
        'lg': 'none',
        'xl': 'none',
        '2xl': 'none',
      },
      transitionDuration: {
        '0': '0ms',
        '100': '100ms',
      },
      animation: {
        'spin-slow': 'spin 1.5s linear infinite',
      },
    },
  },
  plugins: [],
}
