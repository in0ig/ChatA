<template>
  <div class="dictionary-selector">
    <el-popover
      :visible="showPopover"
      placement="bottom-start"
      :width="400"
      trigger="manual"
      popper-class="dictionary-selector-popover"
    >
      <template #reference>
        <el-input
          :model-value="displayValue"
          placeholder="搜索并选择关联字典"
          :size="size"
          clearable
          readonly
          @click="handleInputClick"
          @clear="handleClear"
        >
          <template #suffix>
            <el-icon class="cursor-pointer">
              <ArrowDown v-if="!showPopover" />
              <ArrowUp v-else />
            </el-icon>
          </template>
        </el-input>
      </template>

      <!-- 字典选择面板 -->
      <div class="dictionary-panel">
        <!-- 搜索框 -->
        <div class="search-section">
          <el-input
            v-model="searchQuery"
            placeholder="搜索字典名称、编码或描述..."
            size="small"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>

        <!-- 字典列表 -->
        <div class="dictionary-list" v-loading="loading">
          <div v-if="filteredDictionaries.length === 0" class="empty-state">
            <el-empty 
              :description="searchQuery ? '未找到匹配的字典' : '暂无可用字典'" 
              :image-size="60"
            />
          </div>
          
          <div v-else class="dictionary-items">
            <div
              v-for="dict in filteredDictionaries"
              :key="dict.id"
              class="dictionary-item"
              :class="{ 'selected': selectedDictionaryId === dict.id }"
              @click="handleSelectDictionary(dict)"
            >
              <div class="dictionary-info">
                <div class="dictionary-header">
                  <span class="dictionary-name">{{ dict.name }}</span>
                  <span class="dictionary-code">{{ dict.code }}</span>
                </div>
                <div v-if="dict.description" class="dictionary-description">
                  {{ dict.description }}
                </div>
              </div>
              <div class="dictionary-actions">
                <el-icon v-if="selectedDictionaryId === dict.id" class="selected-icon">
                  <Check />
                </el-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部操作 -->
        <div class="panel-footer">
          <el-button size="small" @click="handleCancel">取消</el-button>
          <el-button 
            type="primary" 
            size="small" 
            @click="handleConfirm"
            :disabled="!selectedDictionaryId"
          >
            确定
          </el-button>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { ArrowDown, ArrowUp, Search, Check } from '@element-plus/icons-vue'
import { dictionaryApi } from '@/api/dictionaryApi'

// Props
interface Props {
  modelValue?: string | null
  size?: 'large' | 'default' | 'small'
  disabled?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  size: 'default',
  disabled: false,
  placeholder: '搜索并选择关联字典'
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string | null]
  'change': [value: string | null, dictionary: any]
}>()

// 响应式数据
const showPopover = ref(false)
const searchQuery = ref('')
const loading = ref(false)
const dictionaries = ref<any[]>([])
const filteredDictionaries = ref<any[]>([])
const selectedDictionaryId = ref<string | null>(props.modelValue)

// 计算属性
const displayValue = computed(() => {
  if (!selectedDictionaryId.value) return ''
  const dict = dictionaries.value.find(d => d.id === selectedDictionaryId.value)
  return dict ? `${dict.name} (${dict.code})` : ''
})

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  selectedDictionaryId.value = newValue
})

// 监听选中值变化
watch(selectedDictionaryId, (newValue) => {
  if (newValue !== props.modelValue) {
    const selectedDict = dictionaries.value.find(d => d.id === newValue)
    emit('update:modelValue', newValue)
    emit('change', newValue, selectedDict)
  }
})

// 方法
const loadDictionaries = async () => {
  loading.value = true
  try {
    // 使用 dictionaryApi 获取字典列表
    const response = await dictionaryApi.getDictionaries()
    if (response.success && response.data) {
      dictionaries.value = response.data
      filteredDictionaries.value = dictionaries.value
    } else {
      console.warn('加载字典列表失败:', response.error)
      dictionaries.value = []
      filteredDictionaries.value = []
    }
  } catch (error) {
    console.error('加载字典列表失败:', error)
    dictionaries.value = []
    filteredDictionaries.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  if (!searchQuery.value.trim()) {
    filteredDictionaries.value = dictionaries.value
    return
  }

  const query = searchQuery.value.toLowerCase()
  filteredDictionaries.value = dictionaries.value.filter(dict => 
    dict.name.toLowerCase().includes(query) ||
    dict.code.toLowerCase().includes(query) ||
    (dict.description && dict.description.toLowerCase().includes(query))
  )
}

const handleInputClick = () => {
  if (props.disabled) return
  showPopover.value = !showPopover.value
  if (showPopover.value) {
    // 重置搜索
    searchQuery.value = ''
    filteredDictionaries.value = dictionaries.value
  }
}

const handleSelectDictionary = (dict: any) => {
  selectedDictionaryId.value = dict.id
}

const handleConfirm = () => {
  showPopover.value = false
}

const handleCancel = () => {
  // 恢复到原始值
  selectedDictionaryId.value = props.modelValue
  showPopover.value = false
}

const handleClear = () => {
  selectedDictionaryId.value = null
}

// 点击外部关闭弹窗
const handleClickOutside = () => {
  if (showPopover.value) {
    handleCancel()
  }
}

// 生命周期
onMounted(async () => {
  await loadDictionaries()
  
  // 添加全局点击事件监听
  document.addEventListener('click', handleClickOutside)
})

// 清理事件监听
import { onUnmounted } from 'vue'
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.dictionary-selector {
  width: 100%;
}

.dictionary-panel {
  padding: 0;
  max-height: 400px;
  display: flex;
  flex-direction: column;
}

.search-section {
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.dictionary-list {
  flex: 1;
  min-height: 200px;
  max-height: 300px;
  overflow-y: auto;
}

.empty-state {
  padding: 20px;
  text-align: center;
}

.dictionary-items {
  padding: 8px 0;
}

.dictionary-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #f5f7fa;
}

.dictionary-item:hover {
  background-color: #f5f7fa;
}

.dictionary-item.selected {
  background-color: #e6f7ff;
  border-color: #409eff;
}

.dictionary-item:last-child {
  border-bottom: none;
}

.dictionary-info {
  flex: 1;
  min-width: 0;
}

.dictionary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.dictionary-name {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.dictionary-code {
  font-size: 12px;
  color: #909399;
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 3px;
}

.dictionary-description {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dictionary-actions {
  flex-shrink: 0;
  margin-left: 8px;
}

.selected-icon {
  color: #409eff;
  font-size: 16px;
}

.panel-footer {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.cursor-pointer {
  cursor: pointer;
}

/* 自定义滚动条 */
.dictionary-list::-webkit-scrollbar {
  width: 6px;
}

.dictionary-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.dictionary-list::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.dictionary-list::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>

<style>
.dictionary-selector-popover {
  padding: 0 !important;
}
</style>