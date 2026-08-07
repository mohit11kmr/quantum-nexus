/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#0D1322',
        'surface-2': '#111a2e',
        'surface-3': '#16213a',
        borderline: 'rgba(255,255,255,0.08)',
        primary: '#00F5A0',
        'primary-dark': '#00D284',
        danger: '#FF3366',
        gold: '#FFD700',
        info: '#38BDF8',
        violet: '#A855F7',
        secondary: '#94A3B8',
      },
      fontFamily: {
        sans: ['Outfit', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        card: '0 4px 20px rgba(0,0,0,0.3)',
        'card-hover': '0 8px 30px rgba(0,0,0,0.4)',
        glow: '0 0 20px rgba(0,245,160,0.25)',
      },
    },
  },
  plugins: [],
};
