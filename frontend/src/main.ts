//引入createApp用于创建应用
import { createApp } from 'vue'
import { createPinia } from 'pinia'
//引入App根组件
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'

// 导入样式
import './styles/main.css'
import '@mdi/font/css/materialdesignicons.min.css'
import '@fortawesome/fontawesome-free/css/all.css'
import 'vuetify/styles'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(vuetify)

//创建应用实例对象并挂载
app.mount('#app')

