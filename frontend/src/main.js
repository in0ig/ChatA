import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { registerElementPlus } from './plugins/element-plus.ts'
import './styles/element-plus-theme.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
registerElementPlus(app)
app.mount('#app')
