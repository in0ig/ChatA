import type { DataTable, TableField, ApiResponse } from '@/types/dataPreparation'
import { apiClient } from '@/api/index'

export const dataTableApi = {
  // 数据表管理
  async getDataTables(): Promise<ApiResponse<DataTable[]>> {
    try {
      const response = await apiClient.get('/api/data-tables')
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch data tables'
      }
    }
  },

  async getDataTablesByDataSource(dataSourceId: number): Promise<ApiResponse<DataTable[]>> {
    try {
      const response = await apiClient.get(`/api/datasources/${dataSourceId}/tables`)
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch data tables by data source'
      }
    }
  },

  async createDataTable(dataTable: Omit<DataTable, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<DataTable>> {
    try {
      const response = await apiClient.post('/api/data-tables', dataTable)
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to create data table'
      }
    }
  },

  async updateDataTable(id: number, dataTable: Partial<DataTable>): Promise<ApiResponse<DataTable>> {
    try {
      const response = await apiClient.put(`/api/data-tables/${id}`, dataTable)
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to update data table'
      }
    }
  },

  async deleteDataTable(id: number): Promise<ApiResponse<void>> {
    try {
      await apiClient.delete(`/api/data-tables/${id}`)
      return {
        success: true,
        message: 'Data table deleted successfully'
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to delete data table'
      }
    }
  },

  // 表字段管理
  async getTableFields(tableId: number): Promise<ApiResponse<TableField[]>> {
    try {
      const response = await apiClient.get(`/api/data-tables/${tableId}/fields`)
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch table fields'
      }
    }
  },

  async getAllTableFields(): Promise<ApiResponse<TableField[]>> {
    try {
      const response = await apiClient.get('/api/table-fields')
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch all table fields'
      }
    }
  },

  async createTableField(field: Omit<TableField, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<TableField>> {
    try {
      const response = await apiClient.post('/api/table-fields', field)
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to create table field'
      }
    }
  },

  async updateTableField(id: number, field: Partial<TableField>): Promise<ApiResponse<TableField>> {
    try {
      const response = await apiClient.put(`/api/table-fields/${id}`, field)
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to update table field'
      }
    }
  },

  async deleteTableField(id: number): Promise<ApiResponse<void>> {
    try {
      await apiClient.delete(`/api/table-fields/${id}`)
      return {
        success: true,
        message: 'Table field deleted successfully'
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to delete table field'
      }
    }
  }
}