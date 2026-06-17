/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        graphite: '#0a0a0a',
        sidebar: '#111111',
        chat: '#1a1a1a',
        ink: '#f5f5f5',
        accent: '#8b5cf6',
      },
    },
  },
  plugins: [],
};
