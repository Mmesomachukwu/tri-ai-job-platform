/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // TRI AI Match brand palette - white background dominant,
        // black for primary text, gold as the main brand accent,
        // orange used sparingly for secondary highlights.
        brand: {
          gold: '#C9A227',
          'gold-dark': '#A6841E',
          orange: '#E1670E',
          black: '#1A1A1A',
          ink: '#2B2B2B',
          border: '#E5E1D8',
          surface: '#FAF9F6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
