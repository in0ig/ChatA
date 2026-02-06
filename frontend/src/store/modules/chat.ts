/**
 * 聊天状态管理 Store
 */
import { defineStore } from 'pinia'
import type { ChatState, ChatSession, ChatMessage, WSMessage } from '@/types/chat'

export const useChatStore = defineStore('chat', {
  state: (): ChatState => ({
    currentSessionId: null,
    sessions: {},
    isConnected: false,
    isStreaming: false,
    error: null,
    chatMode: 'query' as 'query' | 'report', // 'query' = 智能问数, 'report' = 生成报告
    dataSource: [], // 当前选择的数据源 ID 列表
    selectedDataTables: [] // 当前选择的数据表 ID 列表
  }),

  getters: {
    // 获取当前会话
    currentSession(state): ChatSession | null {
      if (!state.currentSessionId) return null
      return state.sessions[state.currentSessionId] || null
    },

    // 获取当前会话的消息列表
    currentMessages(state): ChatMessage[] {
      const session = this.currentSession
      return session?.messages || []
    },

    // 获取所有会话列表
    sessionList(state): ChatSession[] {
      return Object.values(state.sessions).sort((a, b) => b.updatedAt - a.updatedAt)
    }
  },

  actions: {
    // 创建新会话
    createSession(title: string = '新对话'): string {
      const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      const session: ChatSession = {
        id: sessionId,
        title,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        messages: []
      }
      this.sessions[sessionId] = session
      this.currentSessionId = sessionId
      return sessionId
    },

    // 切换会话
    switchSession(sessionId: string) {
      if (this.sessions[sessionId]) {
        this.currentSessionId = sessionId
      }
    },

    // 删除会话
    deleteSession(sessionId: string) {
      delete this.sessions[sessionId]
      if (this.currentSessionId === sessionId) {
        const sessions = this.sessionList
        this.currentSessionId = sessions.length > 0 ? sessions[0].id : null
      }
    },

    // 添加消息
    addMessage(message: Omit<ChatMessage, 'id' | 'timestamp'>): string {
      if (!this.currentSessionId) {
        this.createSession()
      }

      const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      const newMessage: ChatMessage = {
        ...message,
        id: messageId,
        timestamp: Date.now()
      }

      const session = this.sessions[this.currentSessionId!]
      session.messages.push(newMessage)
      session.updatedAt = Date.now()

      return messageId
    },

    // 更新消息
    updateMessage(messageId: string, updates: Partial<ChatMessage>) {
      if (!this.currentSessionId) return

      const session = this.sessions[this.currentSessionId]
      const messageIndex = session.messages.findIndex(m => m.id === messageId)
      
      if (messageIndex !== -1) {
        session.messages[messageIndex] = {
          ...session.messages[messageIndex],
          ...updates
        }
        session.updatedAt = Date.now()
      }
    },

    // 追加消息内容（用于流式输出）
    appendMessageContent(messageId: string, content: string) {
      if (!this.currentSessionId) return

      const session = this.sessions[this.currentSessionId]
      const message = session.messages.find(m => m.id === messageId)
      
      if (message) {
        message.content += content
        session.updatedAt = Date.now()
      }
    },

    // 设置连接状态
    setConnected(connected: boolean) {
      this.isConnected = connected
    },

    // 设置流式状态
    setStreaming(streaming: boolean) {
      this.isStreaming = streaming
    },

    // 设置错误
    setError(error: string | null) {
      this.error = error
    },

    // 清空当前会话
    clearCurrentSession() {
      if (this.currentSessionId) {
        this.sessions[this.currentSessionId].messages = []
      }
    },

    // 编辑消息
    editMessage(messageId: string, newContent: string) {
      if (!this.currentSessionId) return

      const session = this.sessions[this.currentSessionId]
      const message = session.messages.find(m => m.id === messageId)
      
      if (message) {
        message.content = newContent
        session.updatedAt = Date.now()
      }
    },

    // 重发消息
    resendMessage(messageId: string) {
      if (!this.currentSessionId) return

      const session = this.sessions[this.currentSessionId]
      const message = session.messages.find(m => m.id === messageId)
      
      if (message) {
        message.status = 'sending'
        message.timestamp = Date.now()
        session.updatedAt = Date.now()
      }
    },

    // 回溯到消息
    rollbackToMessage(messageId: string) {
      if (!this.currentSessionId) return

      const session = this.sessions[this.currentSessionId]
      const messageIndex = session.messages.findIndex(m => m.id === messageId)
      
      if (messageIndex !== -1) {
        // 删除该消息之后的所有消息
        session.messages = session.messages.slice(0, messageIndex + 1)
        session.updatedAt = Date.now()
      }
    },

    // 导出消息
    exportMessage(messageId: string, format: string) {
      // 导出逻辑在组件中处理，这里只记录操作
      console.log(`Exporting message ${messageId} as ${format}`)
    },

    // 分享消息
    shareMessage(messageId: string, method: string) {
      // 分享逻辑在组件中处理，这里只记录操作
      console.log(`Sharing message ${messageId} via ${method}`)
    },

    // 切换聊天模式
    toggleChatMode() {
      this.chatMode = this.chatMode === 'query' ? 'report' : 'query'
    },

    // 设置数据源
    setDataSource(dataSourceIds: string | string[]) {
      // 支持单个字符串或数组
      this.dataSource = Array.isArray(dataSourceIds) ? dataSourceIds : [dataSourceIds]
    },

    // 设置数据表
    setDataTables(tableIds: string[]) {
      this.selectedDataTables = tableIds
    },

    // 发送消息
    async sendMessage(content: string) {
      // 添加用户消息
      this.addMessage({
        role: 'user',
        content,
        status: 'sent'
      })

      // 这里应该调用 API 发送消息
      // 暂时只是添加一个占位的 AI 响应
      this.addMessage({
        role: 'assistant',
        content: '这是一个占位响应。实际应用中，这里应该调用后端 API。',
        status: 'sent'
      })
    },

    // 加载会话列表
    async loadSessions() {
      // 这里应该从后端加载会话列表
      // 暂时只是一个占位方法
      console.log('Loading sessions...')
    },

    // 加载历史记录
    async loadHistory() {
      // 这里应该从后端加载历史记录
      // 暂时只是一个占位方法
      console.log('Loading history...')
    }
  }
})
