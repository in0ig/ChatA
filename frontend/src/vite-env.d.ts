/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_BASE_API: string
  // 更多环境变量...
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}