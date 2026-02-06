import type { Dictionary, DictionaryItem, ApiResponse } from '@/types/dataPreparation'
import { apiClient } from '@/api/index'

export const dictionaryApi = {
  // 字典管理
  async getDictionaries(): Promise<ApiResponse<Dictionary[]>> {
    try {
      const response = await apiClient.get('/dictionaries/')
      const data = response?.data || response || []
      return {
        success: true,
        data: Array.isArray(data) ? data : []
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch dictionaries'
      }
    }
  },

  async createDictionary(dictionary: Omit<Dictionary, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<Dictionary>> {
    try {
      const response = await apiClient.post('/dictionaries/', dictionary)
      const data = response?.data || response
      return {
        success: true,
        data: data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to create dictionary'
      }
    }
  },

  async updateDictionary(id: string, dictionary: Partial<Dictionary>): Promise<ApiResponse<Dictionary>> {
    try {
      const response = await apiClient.put(`/dictionaries/${id}`, dictionary)
      const data = response?.data || response
      return {
        success: true,
        data: data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to update dictionary'
      }
    }
  },

  async deleteDictionary(id: string): Promise<ApiResponse<void>> {
    try {
      await apiClient.delete(`/dictionaries/${id}`)
      return {
        success: true,
        message: 'Dictionary deleted successfully'
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to delete dictionary'
      }
    }
  },

  // 字典项管理
  async getDictionaryItems(dictionaryId: string): Promise<ApiResponse<DictionaryItem[]>> {
    try {
      console.log('📡 API - getDictionaryItems: calling for dictionaryId:', dictionaryId)
      const url = `/dictionaries/${dictionaryId}/items`
      console.log('📡 API - getDictionaryItems: full URL:', url)
      const response = await apiClient.get(url)
      console.log('📡 API - getDictionaryItems: raw response:', response)
      const data = response?.data || response || []
      console.log('📡 API - getDictionaryItems: processed data:', data)
      return {
        success: true,
        data: Array.isArray(data) ? data : []
      }
    } catch (error: any) {
      console.error('❌ API - getDictionaryItems: error:', error)
      return {
        success: false,
        error: error.message || 'Failed to fetch dictionary items'
      }
    }
  },

  async getAllDictionaryItems(): Promise<ApiResponse<DictionaryItem[]>> {
    try {
      const response = await apiClient.get('/dictionary-items')
      const data = response?.data || response || []
      return {
        success: true,
        data: Array.isArray(data) ? data : []
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to fetch all dictionary items'
      }
    }
  },

  async createDictionaryItem(item: Omit<DictionaryItem, 'id' | 'created_at' | 'updated_at'>): Promise<ApiResponse<DictionaryItem>> {
    try {
      // 使用正确的API路径：/dictionaries/{dictionaryId}/items
      const dictionaryId = item.dictionary_id
      if (!dictionaryId) {
        throw new Error('Dictionary ID is required')
      }
      const response = await apiClient.post(`/dictionaries/${dictionaryId}/items`, item)
      const data = response?.data || response
      return {
        success: true,
        data: data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to create dictionary item'
      }
    }
  },

  async updateDictionaryItem(id: string, item: Partial<DictionaryItem>): Promise<ApiResponse<DictionaryItem>> {
    try {
      // 使用正确的API路径：/dictionaries/{dictionaryId}/items/{itemId}
      const dictionaryId = item.dictionary_id
      if (!dictionaryId) {
        throw new Error('Dictionary ID is required')
      }
      const response = await apiClient.put(`/dictionaries/${dictionaryId}/items/${id}`, item)
      const data = response?.data || response
      return {
        success: true,
        data: data
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to update dictionary item'
      }
    }
  },

  async deleteDictionaryItem(id: string, dictionaryId: string): Promise<ApiResponse<void>> {
    try {
      await apiClient.delete(`/dictionaries/${dictionaryId}/items/${id}`)
      return {
        success: true,
        message: 'Dictionary item deleted successfully'
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to delete dictionary item'
      }
    }
  },

  // 导入导出功能
  async importDictionary(file: File): Promise<ApiResponse<void>> {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await apiClient.post('/dictionaries/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      const data = response?.data || response
      
      return {
        success: true,
        message: data?.message || 'Dictionary imported successfully'
      }
    } catch (error: any) {
      return {
        success: false,
        error: error.message || 'Failed to import dictionary'
      }
    }
  },

  async exportDictionary(dictionaryId: string): Promise<Blob> {
    const response = await apiClient.get(`/dictionaries/${dictionaryId}/export`, {
      responseType: 'blob'
    })
    return response?.data || response
  }
}