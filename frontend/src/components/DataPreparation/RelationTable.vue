<template>
  <div class="relation-table-container">
    <div class="table-toolbar">
      <el-input
        v-model="search"
        placeholder="搜索关联关系"
        class="search-input"
        :prefix-icon="Search"
        clearable
      />
      <el-button type="primary" :icon="Plus" @click="handleCreate">新建关联</el-button>
    </div>

    <el-table :data="filteredData" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="mainTable" label="主表" />
      <el-table-column prop="relatedTable" label="从表" />
      <el-table-column prop="joinType" label="关联类型" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-popconfirm
            title="确定删除此关联关系吗？"
            @confirm="handleDelete(row)"
          >
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="table-pagination"
      :current-page="currentPage"
      :page-size="pageSize"
      :total="total"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="50%">
      <!-- RelationForm will be rendered here -->
      <div class="form-container">
        <slot name="form" :formData="currentRelation" :isEdit="isEdit" />
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { ElInput, ElButton, ElTable, ElTableColumn, ElPagination, ElPopconfirm, ElDialog } from 'element-plus';
import { Search, Plus } from '@element-plus/icons-vue';

interface Relation {
  id: number;
  mainTable: string;
  relatedTable: string;
  joinType: 'INNER' | 'LEFT' | 'RIGHT';
  description: string;
}

const search = ref('');
const loading = ref(true);
const relations = ref<Relation[]>([]);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);

const dialogVisible = ref(false);
const dialogTitle = ref('');
const isEdit = ref(false);
const currentRelation = ref<Relation | null>(null);
const submitting = ref(false);

const filteredData = computed(() =>
  relations.value.filter(data =>
    !search.value ||
    data.mainTable.toLowerCase().includes(search.value.toLowerCase()) ||
    data.relatedTable.toLowerCase().includes(search.value.toLowerCase())
  )
);

const fetchRelations = () => {
  loading.value = true;
  // Mock API call
  setTimeout(() => {
    const mockData: Relation[] = [
      { id: 1, mainTable: 'orders', relatedTable: 'users', joinType: 'LEFT', description: '订单关联用户' },
      { id: 2, mainTable: 'orders', relatedTable: 'products', joinType: 'INNER', description: '订单关联产品' },
    ];
    relations.value = mockData;
    total.value = mockData.length;
    loading.value = false;
  }, 500);
};

onMounted(() => {
  fetchRelations();
});

const handleCreate = () => {
  isEdit.value = false;
  dialogTitle.value = '新建关联关系';
  currentRelation.value = null;
  dialogVisible.value = true;
};

const handleEdit = (row: Relation) => {
  isEdit.value = true;
  dialogTitle.value = '编辑关联关系';
  currentRelation.value = { ...row };
  dialogVisible.value = true;
};

const handleDelete = (row: Relation) => {
  console.log('Delete relation:', row.id);
  // Call API to delete, then refetch
  fetchRelations();
};

const handleSizeChange = (val: number) => {
  pageSize.value = val;
  fetchRelations();
};

const handleCurrentChange = (val: number) => {
  currentPage.value = val;
  fetchRelations();
};

const submitForm = async () => {
  submitting.value = true;
  
  try {
    // 通过事件通知父组件获取表单数据
    const event = new CustomEvent('submit-form', {
      detail: { isEdit: isEdit.value, currentRelation: currentRelation.value }
    });
    
    // 简化版本：直接使用 slot 中的表单数据
    // 在实际应用中，这里应该调用 API
    console.log('提交表单数据:', {
      isEdit: isEdit.value,
      formData: currentRelation.value
    });
    
    // TODO: 实际的 API 调用
    // if (isEdit.value) {
    //   await relationApi.updateRelation(currentRelation.value.id, formData);
    // } else {
    //   await relationApi.createRelation(formData);
    // }
    
    dialogVisible.value = false;
    await fetchRelations();
  } catch (error) {
    console.error('提交表单时出错:', error);
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
.relation-table-container {
  padding: 20px;
}
.table-toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
.search-input {
  width: 300px;
}
.table-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
