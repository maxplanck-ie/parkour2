import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import dutiesApp from './dutiesApp.vue'
import dutiesRouter from './router/dutiesRouter.js'

const app = createApp(dutiesApp)

app.use(createPinia())
app.use(dutiesRouter)

app.mount('#app')
