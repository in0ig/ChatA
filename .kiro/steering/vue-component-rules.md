---
inclusion: fileMatch
fileMatchPattern: '*.vue'
---

# Vue 组件开发规则

当你在编辑 `.vue` 文件时，这些规则会自动应用。

## 组件结构

使用标准的 Vue 3 SFC 结构：

```vue
<template>
  <!-- UI 模板 -->
</template>

<script setup lang="ts">
// 导入
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUIStore } from '@/store/modules/ui'

// Props 定义
interface Props {
  title?: string
}
const props = withDefaults(defineProps<Props>(), {
  title: '默认标题'
})

// Emits 定义
const emit = defineEmits<{
  submit: [value: string]
  cancel: []
}>()

// 响应式状态
const count = ref(0)

// 计算属性
const doubleCount = computed(() => count.value * 2)

// 方法
const handleClick = () => {
  emit('submit', 'value')
}
</script>

<style scoped>
/* 组件样式 */
</style>
```

## 最佳实践

### 1. Props 验证
- 使用 TypeScript interface 定义 Props
- 使用 `withDefaults` 提供默认值
- 可选属性使用 `?` 标记

### 2. Emits 定义
- 明确定义所有 emit 事件
- 使用 TypeScript 类型标注参数

### 3. 响应式数据
- 使用 `ref` 定义基础类型
- 使用 `reactive` 定义对象类型
- 使用 `computed` 定义计算属性

### 4. Store 使用
```typescript
import { useUIStore } from '@/store/modules/ui'
import { useChatStore } from '@/store/modules/chat'

const uiStore = useUIStore()
const chatStore = useChatStore()

// 访问状态
console.log(uiStore.isLoading)

// 调用 actions
uiStore.showToast('成功', 'success')
```

### 5. 路由使用
```typescript
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

// 导航
router.push('/data-prep/sources')

// 获取参数
const tableId = route.params.tableId
```

## Element Plus 组件使用

### 常用组件
- `<el-button>` - 按钮
- `<el-input>` - 输入框
- `<el-select>` - 选择器
- `<el-table>` - 表格
- `<el-dialog>` - 对话框
- `<el-drawer>` - 抽屉
- `<el-message>` - 消息提示

### 示例
```vue
<template>
  <el-button type="primary" @click="handleClick">
    提交
  </el-button>
  
  <el-input 
    v-model="inputValue" 
    placeholder="请输入内容"
  />
</template>
```

## 样式规范

### 使用 scoped 样式
```vue
<style scoped>
.container {
  padding: 20px;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #333;
}
</style>
```

### 主题色
- 主色: `#1890ff`
- 成功: `#52c41a`
- 警告: `#faad14`
- 错误: `#f5222d`
- 文本: `#333333`
- 次要文本: `#666666`
- 边框: `#d9d9d9`
- 背景: `#f5f5f5`

## 测试要求

每个 Vue 组件必须有对应的测试文件：

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import MyComponent from '@/components/MyComponent.vue'

describe('MyComponent', () => {
  it('should render correctly', () => {
    const wrapper = mount(MyComponent, {
      global: {
        plugins: [createPinia()]
      }
    })
    expect(wrapper.exists()).toBe(true)
  })
  
  it('should emit event when button clicked', async () => {
    const wrapper = mount(MyComponent, {
      global: {
        plugins: [createPinia()]
      }
    })
    
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('submit')).toBeTruthy()
  })
})
```

## 性能优化

- 使用 `v-show` 而非 `v-if` 用于频繁切换
- 使用 `v-once` 用于静态内容
- 大列表使用虚拟滚动
- 使用 `computed` 缓存计算结果
- 避免在模板中使用复杂表达式
