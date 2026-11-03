import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    fs: {
      // images/ is a symlink to the shared ../images folder
      allow: ['..'],
    },
  },
})
