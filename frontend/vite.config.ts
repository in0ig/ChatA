import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue({
      include: [/\.vue$/, /\.md$/],
      template: {
        compilerOptions: {
          // 只对真正需要的自定义元素进行标记
          isCustomElement: (tag) => [
            'search',
            'setting', 
            'bell',
            'document',
            'chart-line',
            'language',
            'el-icon'
          ].includes(tag)
        }
      }
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  },
  publicDir: false
})