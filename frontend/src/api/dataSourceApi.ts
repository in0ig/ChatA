import type { DataSource, ApiResponse } from '@/types/dataPreparation'
import { apiClient } from '@/api/index'

export const dataSourceApi = {
  // 数据源管理
  async getDataSources(): Promise<ApiResponse<DataSource[]>> {
    try {
      const response = await apiClient.get('/api/datasources')
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch data sources'
      }
    }
  },

  async createDataSource(dataSource: Omit<DataSource, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<DataSource>> {
    try {
      const response = await apiClient.post('/api/datasources', dataSource)
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to create data source'
      }
    }
  },

  async updateDataSource(id: number, dataSource: Partial<DataSource>): Promise<ApiResponse<DataSource>> {
    try {
      const response = await apiClient.put(`/api/datasources/${id}`, dataSource)
      return {
        success: true,
        data: response.data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to update data source'
      }
    }
  },

  async deleteDataSource(id: number): Promise<ApiResponse<void>> {
    try {
      await apiClient.delete(`/api/datasources/${id}`)
      return {
        success: true,
        message: 'Data source deleted successfully'
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to delete data source'
      }
    }
  },

  async testConnection(dataSource: Partial<DataSource>): Promise<ApiResponse<boolean>> {
    try {
      const response = await apiClient.post('/api/datasources/test-connection', dataSource)
      return {
        success: true,
        data: response.data.success || false
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to test connection'
      }
    }
  }
}