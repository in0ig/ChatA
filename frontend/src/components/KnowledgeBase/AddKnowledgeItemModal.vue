<template>
  <el-dialog
    title="新增知识"
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
      <!-- 移除了知识类型选择器，类型由知识库决定 -->

      <el-form-item label="知识名称" prop="name" v-if="props.knowledgeBaseType === 'TERM'">
        <el-input 
          v-model="form.name" 
          placeholder="请输入名称（如：毛利润）"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="事件时间" prop="dateRange" v-if="props.knowledgeBaseType === 'EVENT'">
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
      
      <el-form-item label="提问示例" prop="exampleQuestion" v-if="props.knowledgeBaseType !== 'EVENT'">
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
      <el-button type="primary" @click="handleSubmit">确定</el-button>
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
  knowledgeBaseId: {
    type: [Number, String],
    required: true
  },
  knowledgeBaseType: {
    type: String,
    required: true,
    validator: (value) => ['TERM', 'LOGIC', 'EVENT'].includes(value)
  }
})

const emit = defineEmits(['update:visible', 'submit'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const form = reactive({
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

const getExplanationPlaceholder = () => {
  switch (props.knowledgeBaseType) {
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
  switch (props.knowledgeBaseType) {
    case 'TERM':
      return '用户可能会如何询问这个名词？（如：什么是毛利润？）'
    case 'LOGIC':
      return '用户可能会如何询问这个逻辑？（如：默认查询多长时间的数据？）'
    default:
      return '请输入示例问题'
  }
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    form.name = ''
    form.explanation = ''
    form.exampleQuestion = ''
    form.dateRange = null
  }
})

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = () => {
  formRef.value.validate((valid) => {
    if (valid) {
      // 构建符合后端 API 的数据格式（使用 snake_case）
      const newItem = {
        knowledge_base_id: props.knowledgeBaseId.toString(),
        type: props.knowledgeBaseType,
        name: props.knowledgeBaseType === 'TERM' ? form.name : null,
        explanation: form.explanation,
        example_question: props.knowledgeBaseType !== 'EVENT' ? (form.exampleQuestion || null) : null,
        event_date_start: props.knowledgeBaseType === 'EVENT' && form.dateRange ? form.dateRange[0] : null,
        event_date_end: props.knowledgeBaseType === 'EVENT' && form.dateRange ? form.dateRange[1] : null
      }
      
      emit('submit', newItem)
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
