/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  // Use a prefix to avoid conflicts with LeetCode's own Tailwind styles
  prefix: 'lc-',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        coach: {
          bg: '#FFFFFF',
          surface: '#F8F9FA',
          border: '#E5E7EB',
          'border-hover': '#D1D5DB',
          text: '#111827',
          'text-secondary': '#6B7280',
          'text-muted': '#9CA3AF',
          accent: '#4F46E5',          // indigo-600
          'accent-hover': '#4338CA',  // indigo-700
          'accent-light': '#EEF2FF', // indigo-50
          success: '#059669',         // emerald-600
          warning: '#D97706',         // amber-600
          danger: '#DC2626',          // red-600
          l1: '#3B82F6',              // blue-500 – Level 1 hint
          l2: '#8B5CF6',              // violet-500 – Level 2 hint
          l3: '#EC4899',              // pink-500 – Level 3 hint
          upgrade: '#059669',         // emerald-600 – Upgrade
        },
      },
      boxShadow: {
        'panel': '0 4px 24px -2px rgba(0,0,0,0.10), 0 1px 4px -1px rgba(0,0,0,0.06)',
        'panel-hover': '0 8px 32px -4px rgba(0,0,0,0.14), 0 2px 8px -2px rgba(0,0,0,0.08)',
        'btn': '0 1px 2px rgba(0,0,0,0.06)',
      },
      borderRadius: {
        'panel': '12px',
        'btn': '8px',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s cubic-bezier(0.22, 1, 0.36, 1)',
        'pulse-dot': 'pulseDot 1.4s ease-in-out infinite',
        'spin-slow': 'spin 2s linear infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        pulseDot: {
          '0%, 80%, 100%': { transform: 'scale(0)', opacity: '0.5' },
          '40%':            { transform: 'scale(1)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};
