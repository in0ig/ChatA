<template>
  <el-dialog
    title="创建知识库"
    v-model="dialogVisible"
    width="800px"
    @close="handleClose"
  >
    <el-form
      :model="form"
      :rules="rules"
      ref="formRef"
      label-width="120px"
      class="knowledge-base-form"
    >
      <div class="form-container">
        <!-- 左侧表单区域 -->
        <div class="form-section">
          <el-form-item label="知识库名称" prop="name">
            <el-input v-model="form.name" placeholder="请输入知识库名称" />
          </el-form-item>

          <el-form-item label="知识库类型" prop="type">
            <el-radio-group v-model="form.type" direction="horizontal">
              <el-radio value="TERM" border>名词</el-radio>
              <el-radio value="LOGIC" border>业务逻辑</el-radio>
              <el-radio value="EVENT" border>事件</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="生效范围" prop="scope">
            <el-radio-group v-model="form.scope" direction="horizontal">
              <el-radio value="GLOBAL" border>全局</el-radio>
              <el-radio value="TABLE" border>表级</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="启用状态" prop="status">
            <el-radio-group v-model="form.status" direction="horizontal">
              <el-radio :value="true" border>启用</el-radio>
              <el-radio :value="false" border>禁用</el-radio>
            </el-radio-group>
          </el-form-item>

          <el-form-item label="关联数据表" v-if="form.scope === 'TABLE'">
            <el-select
              v-model="form.table_id"
              placeholder="请选择关联的数据表"
              style="width: 100%"
            >
              <el-option
                v-for="table in mockTables"
                :key="table.value"
                :label="table.label"
                :value="table.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="描述">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="4"
              placeholder="请输入知识库的详细描述"
            />
          </el-form-item>
        </div>

        <!-- 右侧说明区域 -->
        <div class="info-section">
          <div class="info-content">
            <p v-if="form.type === 'TERM'">录入毛利润、转化率、客单价等业务常用的专有名词和解释</p>
            <p v-else-if="form.type === 'LOGIC'">录入默认查询时间范围、库存预警阈值、绩效考核周期等业务逻辑知识。业务逻辑知识过多会影响问答效果，每张数据表的业务逻辑条数推荐不要超过30条</p>
            <p v-else-if="form.type === 'EVENT'">录入2024年春节促销活动、系统升级维护等事件知识。事件知识仅在波动归因模块生效。知识过多会影响问答效果，每张数据表的知识条数推荐不要超过30条</p>
            <p v-else>请选择知识库类型以查看相关说明</p>
          </div>
        </div>
      </div>
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
  }
})

const emit = defineEmits(['update:visible', 'submit'])

// 内部对话框可见性状态
const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

// 表单数据
const form = reactive({
  name: '',
  type: '',
  scope: 'GLOBAL',
  status: true,
  table_id: '',
  description: ''
})

// 表单验证规则
const rules = reactive({
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择知识库类型', trigger: 'change' }
  ],
  scope: [
    { required: true, message: '请选择生效范围', trigger: 'change' }
  ]
})

// Mock 数据表列表
const mockTables = ref([
  { value: 'sales_data', label: '销售数据表' },
  { value: 'product_info', label: '产品信息表' },
  { value: 'customer_info', label: '客户信息表' },
  { value: 'inventory', label: '库存表' },
  { value: 'finance_report', label: '财务报表' },
  { value: 'marketing_campaign', label: '营销活动表' }
])

// 表单引用
const formRef = ref(null)

// 当生效范围为全局时，清空关联数据表
watch(() => form.scope, (newVal) => {
  if (newVal === 'GLOBAL') {
    form.table_id = ''
  }
})

// 关闭弹窗
const handleClose = () => {
  // 重置表单
  formRef.value?.resetFields()
  // 手动重置所有字段
  form.name = ''
  form.type = ''
  form.scope = 'GLOBAL'
  form.status = true
  form.table_id = ''
  form.description = ''
  
  emit('update:visible', false)
}

// 提交表单
const handleSubmit = () => {
  formRef.value.validate((valid) => {
    if (valid) {
      // 创建知识库对象（不包含 id，由后端生成）
      const newKnowledgeBase = {
        name: form.name,
        description: form.description || null,
        type: form.type,
        scope: form.scope,
        status: form.status,
        table_id: form.table_id || null
      }
      
      emit('submit', newKnowledgeBase)
      
      // 提交后重置表单
      formRef.value?.resetFields()
      form.name = ''
      form.type = ''
      form.scope = 'GLOBAL'
      form.status = true
      form.table_id = ''
      form.description = ''
      
      emit('update:visible', false)
    } else {
      console.log('表单验证失败')
      return false
    }
  })
}
</script>

<style scoped>
.knowledge-base-form {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.form-container {
  display: flex;
  height: calc(100% - 60px);
}

.form-section {
  flex: 1;
  padding-right: 30px;
  border-right: 1px solid #eee;
}

.info-section {
  width: 300px;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 4px;
  margin-left: 20px;
  overflow-y: auto;
}

.info-content {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
}

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
