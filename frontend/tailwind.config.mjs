export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        primary: '#1E88E5', // Bright blue from mockups
        secondary: '#8e9eab',
        success: '#2ECA6A', // Green for completed/confirmed
        danger: '#FF5252', // Red for cancelled
        warning: '#F5A623', // Orange for pending
        info: '#00b4d8', 
        dark: '#2c3e50',
        background: '#f8fafc', // Very light gray/blue background
        teal: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d9488',
          700: '#0f766e',
          800: '#115e59',
          900: '#134e4a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};