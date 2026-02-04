<template>
  <el-dialog
    title="编辑知识"
    v-model="dialogVisible"
    width="600px"
    @close="handleClose"
  >
    <el-form
      :model="form"
      :rules="rules"
      ref="formRef"
      label-width="100px"
    >
      <el-form-item label="知识类型">
        <el-tag>{{ getTypeLabel(form.type) }}</el-tag>
      </el-form-item>

      <el-form-item label="知识名称" prop="name" v-if="form.type === 'TERM'">
        <el-input 
          v-model="form.name" 
          placeholder="请输入名称（如：毛利润）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="事件时间" prop="dateRange" v-if="form.type === 'EVENT'">
        <el-date-picker
          v-model="form.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      
      <el-form-item label="解释" prop="explanation">
        <el-input 
          v-model="form.explanation" 
          type="textarea"
          :rows="6"
          :placeholder="getExplanationPlaceholder()"
          maxlength="1500"
          show-word-limit
        />
      </el-form-item>
      
      <el-form-item label="提问示例" prop="exampleQuestion" v-if="form.type !== 'EVENT'">
        <el-input 
          v-model="form.exampleQuestion" 
          type="textarea"
          :rows="3"
          :placeholder="getExamplePlaceholder()"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <div class="dialog-footer">
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit">保存</el-button>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  knowledgeItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'submit'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const form = reactive({
  type: 'TERM',
  name: '',
  explanation: '',
  exampleQuestion: '',
  dateRange: null
})

const rules = reactive({
  name: [
    { required: true, message: '请输入知识名称', trigger: 'blur' }
  ],
  explanation: [
    { required: true, message: '请输入解释', trigger: 'blur' }
  ]
})

const formRef = ref(null)

const getTypeLabel = (type) => {
  const labels = {
    'TERM': '名词',
    'LOGIC': '业务逻辑',
    'EVENT': '事件'
  }
  return labels[type] || '未知'
}

const getExplanationPlaceholder = () => {
  switch (form.type) {
    case 'TERM':
      return '请详细解释这个名词的含义（如：毛利润是指销售收入减去销售成本后的利润）'
    case 'LOGIC':
      return '请描述这个业务逻辑的具体规则（如：默认查询时间范围为最近30天）'
    case 'EVENT':
      return '请描述这个事件的详细情况（如：2024年春节促销活动，销售额增长35%）'
    default:
      return '请输入解释'
  }
}

const getExamplePlaceholder = () => {
  switch (form.type) {
    case 'TERM':
      return '用户可能会如何询问这个名词？（如：什么是毛利润？）'
    case 'LOGIC':
      return '用户可能会如何询问这个逻辑？（如：默认查询多长时间的数据？）'
    default:
      return '请输入示例问题'
  }
}

const initForm = () => {
  if (props.knowledgeItem) {
    form.type = props.knowledgeItem.type
    form.name = props.knowledgeItem.name || ''
    form.explanation = props.knowledgeItem.explanation || ''
    form.exampleQuestion = props.knowledgeItem.example_question || ''
    
    // 将后端的 event_date_start 和 event_date_end 转换为前端的 dateRange
    if (props.knowledgeItem.event_date_start && props.knowledgeItem.event_date_end) {
      form.dateRange = [
        props.knowledgeItem.event_date_start,
        props.knowledgeItem.event_date_end
      ]
    } else {
      form.dateRange = null
    }
  }
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    initForm()
  }
})

watch(() => props.knowledgeItem, () => {
  if (props.visible) {
    initForm()
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = () => {
  formRef.value.validate((valid) => {
    if (valid) {
      // 构建符合后端 API 的数据格式（使用 snake_case）
      const updatedItem = {
        id: props.knowledgeItem.id,
        knowledge_base_id: props.knowledgeItem.knowledge_base_id,
        type: form.type,
        name: form.type === 'TERM' ? form.name : null,
        explanation: form.explanation,
        example_question: form.type !== 'EVENT' ? (form.exampleQuestion || null) : null,
        event_date_start: form.type === 'EVENT' && form.dateRange ? form.dateRange[0] : null,
        event_date_end: form.type === 'EVENT' && form.dateRange ? form.dateRange[1] : null
      }
      
      emit('submit', updatedItem)
      emit('update:visible', false)
    } else {
      console.log('表单验证失败')
      return false
    }
  })
}
</script>

<style scoped>
.el-form-item {
  margin-bottom: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}
</style>
