/**
 * Chat Store - 管理对话状态
 * 对应 PRD 模块 2.2 和 2.3
 */
import { defineStore } from 'pinia'
import { useUIStore } from './ui'
import service from '@/services/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  chartType?: string
  chartData?: any
  actions?: MessageAction[]
}

export interface MessageAction {
  type: 'refresh' | 'like' | 'dislike'
  label: string
  handler: () => void
}

export interface Session {
  id: string
  name: string
  userId: number
  conversation: Message[]
  lastActive: Date
  createdAt: Date
}

// 新增：对话消息接口
export interface ConversationMessage {
  id: string
  turn: number
  role: 'user' | 'assistant'
  content: string
  parentMessageId: string | null
  tokenCount: number
  modelUsed: string
  intent: string
  queryId: string | null
  analysisId: string | null
  createdAt: Date
}

// 新增：会话上下文接口
export interface SessionContext {
  messages: ConversationMessage[]
  tokenCount: number
  summary: string | null
  lastSummaryAt: Date | null
}

// 新增：Token 使用统计接口
export interface TokenUsageStats {
  sessionId: string
  totalTurns: number
  totalInputTokens: number
  totalOutputTokens: number
  totalTokens: number
  modelUsage: Record<string, { input: number, output: number }>
}

export interface ChatState {
  // 当前会话
  currentSessionId: string | null
  sessions: Session[]
  
  // 消息相关
  messages: Message[]
  inputText: string
  
  // 数据源
  currentDataSource: string | null
  
  // 模式：智能问数 vs 生成报告
  chatMode: 'query' | 'report'
  
  // 推荐问题
  recommendedQuestions: string[]
  
  // 查询历史
  queryHistory: Array<{
    id: number
    queryText: string
    result: any
    chartType: string
    createdAt: Date
  }>
  
  // 查询缓存：使用查询文本和数据源 ID 作为键，存储查询结果和时间戳
  queryCache: Map<string, { result: any; timestamp: Date }>
  
  // 新增：对话历史（用于存储完整的对话消息）
  conversationHistory: ConversationMessage[]
  
  // 新增：会话上下文（支持本地模型和阿里云模型）
  sessionContext: {
    local_model: SessionContext
    aliyun_model: SessionContext
  }
  
  // 新增：Token 使用统计
  tokenUsage: TokenUsageStats
}

export const useChatStore = defineStore('chat', {
  state: (): ChatState => ({
    currentSessionId: 'test-session-id', // Initialize with a default session ID for testing
    sessions: [],
    messages: [],
    inputText: '',
    currentDataSource: null,
    chatMode: 'query',
    recommendedQuestions: [
      '2023年各商品类别的销售额是多少？',
      '2024年毛利最高的产品是什么？',
      '最近7天的销售趋势如何？',
      '各区域的销售对比情况',
      '客户转化率的变化趋势'
    ],
    queryHistory: [],
    
    // 初始化查询缓存
    queryCache: new Map(),
    
    // 初始化新字段
    conversationHistory: [],
    sessionContext: {
      local_model: {
        messages: [],
        tokenCount: 0,
        summary: null,
        lastSummaryAt: null
      },
      aliyun_model: {
        messages: [],
        tokenCount: 0,
        summary: null,
        lastSummaryAt: null
      }
    },
    tokenUsage: {
      sessionId: 'test-session-id', // Initialize with a default session ID for testing
      totalTurns: 0,
      totalInputTokens: 0,
      totalOutputTokens: 0,
      totalTokens: 0,
      modelUsage: {}
    }
  }),
  
  getters: {
    // 是否可以发送消息
    canSend: (state) => {
      return state.inputText.trim().length > 0 && state.currentDataSource !== null
    },
    
    // 当前会话
    currentSession: (state) => {
      return state.sessions.find(s => s.id === state.currentSessionId) || null
    },
    
    // 是否有活跃会话
    hasActiveSession: (state) => {
      return state.currentSessionId !== null
    }
  },
  
  actions: {
    // ========== 新增方法 ==========
    
    /**
     * 添加消息到对话历史
     * @param message - 要添加的消息
     */
    addMessage(message: ConversationMessage): void {
      this.conversationHistory.push(message)
      
      // 更新会话上下文中的token计数
      const modelType = message.modelUsed.includes('local') ? 'local_model' : 'aliyun_model'
      this.sessionContext[modelType as keyof typeof this.sessionContext].tokenCount += message.tokenCount
      this.sessionContext[modelType as keyof typeof this.sessionContext].messages.push(message)
      
      // 更新token使用统计
      this.tokenUsage.totalTurns += 1
      this.tokenUsage.totalTokens += message.tokenCount
      
      if (message.role === 'user') {
        this.tokenUsage.totalInputTokens += message.tokenCount
      } else {
        this.tokenUsage.totalOutputTokens += message.tokenCount
      }
      
      // 更新模型使用统计
      if (!this.tokenUsage.modelUsage[message.modelUsed]) {
        this.tokenUsage.modelUsage[message.modelUsed] = { input: 0, output: 0 }
      }
      
      if (message.role === 'user') {
        this.tokenUsage.modelUsage[message.modelUsed].input += message.tokenCount
      } else {
        this.tokenUsage.modelUsage[message.modelUsed].output += message.tokenCount
      }
    },
    
    /**
     * 获取对话历史
     * @returns ConversationMessage[] - 对话历史数组，确保每个项目都有唯一id
     */
    getConversationHistory(): ConversationMessage[] {
      return this.conversationHistory.map(item => {
        // 如果item没有id，生成一个基于时间戳的唯一id
        if (!item.id) {
          return {
            ...item,
            id: `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
          }
        }
        return item
      })
    },
    
    /**
     * 检查Token限制
     * @param modelType - 模型类型：'local' 或 'aliyun'
     * @returns boolean - 是否超过限制
     */
    checkTokenLimit(modelType: 'local' | 'aliyun'): boolean {
      const threshold = modelType === 'local' ? 15000 : 800000
      const modelKey = (modelType + '_model') as keyof typeof this.sessionContext
      const currentTokenCount = this.sessionContext[modelKey].tokenCount
      return currentTokenCount >= threshold
    },
    
    /**
     * 总结会话上下文
     * @param modelType - 模型类型：'local' 或 'aliyun'
     */
    async summarizeContext(modelType: 'local' | 'aliyun'): Promise<void> {
      const modelKey = (modelType + '_model') as keyof typeof this.sessionContext
      const context = this.sessionContext[modelKey]
      
      // 如果没有消息或已总结过，直接返回
      if (context.messages.length === 0 || context.summary) {
        return
      }
      
      // 这里应该调用后端API进行总结，但根据需求，我们只实现逻辑框架
      // 实际实现中，这里会调用后端的总结服务
      
      // 模拟总结过程
      const summaryText = `会话总结：包含${context.messages.length}条消息，总Token数：${context.tokenCount}`
      
      // 更新会话上下文
      context.summary = summaryText
      context.lastSummaryAt = new Date()
      
      // 更新token使用统计中的summary字段
      this.tokenUsage.sessionId = this.currentSessionId || ''
    },
    
    /**
     * 获取Token使用统计
     * @returns TokenUsageStats - Token使用统计信息
     */
    getTokenUsageStats(): TokenUsageStats {
      return {
        ...this.tokenUsage,
        modelUsage: JSON.parse(JSON.stringify(this.tokenUsage.modelUsage))
      }
    },
    
    // ========== 会话管理 ==========
    
    async loadSessions() {
      const uiStore = useUIStore()
      try {
        const response = await service.get('/sessions/')
        const data = response.data || response
        this.sessions = data.map((s: any) => ({
          ...s,
          lastActive: new Date(s.last_active),
          createdAt: new Date(s.created_at)
        }))
      } catch (error) {
        uiStore.showToast((error as Error).message, 'error')
      }
    },
    
    async createSession() {
      const uiStore = useUIStore()
      try {
        const response = await service.post('/sessions', {
          user_id: 1, // TODO: 从用户认证获取
          session_id: null,
          conversation: []
        })
        
        const session = response.data || response
        
        this.sessions.unshift({
          ...session,
          lastActive: new Date(session.last_active),
          createdAt: new Date(session.created_at)
        })
        this.currentSessionId = session.session_id
        this.messages = []
        
        uiStore.showToast('新会话已创建', 'success')
      } catch (error) {
        uiStore.showToast((error as Error).message, 'error')
      }
    },
    
    async switchSession(sessionId: string) {
      this.currentSessionId = sessionId
      const session = this.currentSession
      if (session) {
        this.messages = session.conversation
      }
    },
    
    async deleteSession(sessionId: string) {
      const uiStore = useUIStore()
      try {
        await service.delete(`/sessions/${sessionId}`)
        
        this.sessions = this.sessions.filter(s => s.id !== sessionId)
        if (this.currentSessionId === sessionId) {
          this.currentSessionId = this.sessions[0]?.id || null
        }
        
        uiStore.showToast('会话已删除', 'success')
      } catch (error) {
        uiStore.showToast((error as Error).message, 'error')
      }
    },
    
    // ========== 消息管理 ==========
    
    async sendMessage(text?: string) {
      const uiStore = useUIStore()
      const messageText = text || this.inputText
      
      if (!messageText.trim()) return
      if (!this.currentDataSource) {
        uiStore.showToast('请先选择数据源', 'warning')
        return
      }
      
      // 检查缓存：使用查询文本和数据源 ID 作为键
      const cacheKey = `${messageText.trim()}|${this.currentDataSource}`
      const cachedResult = this.queryCache.get(cacheKey)
      
      if (cachedResult) {
        // 如果缓存存在，直接使用缓存结果
        const aiMessage: Message = {
          id: `msg_${Date.now()}_ai`,
          role: 'assistant',
          content: cachedResult.result.explanation || '查询完成',
          timestamp: new Date(),
          chartType: cachedResult.result.chart_type,
          chartData: cachedResult.result.data,
          actions: [
            { type: 'refresh', label: '刷新', handler: () => this.sendMessage(messageText) },
            { type: 'like', label: '点赞', handler: () => console.log('liked') },
            { type: 'dislike', label: '点踩', handler: () => console.log('disliked') }
          ]
        }
        
        // 添加用户消息
        const userMessage: Message = {
          id: `msg_${Date.now()}`,
          role: 'user',
          content: messageText,
          timestamp: new Date()
        }
        this.messages.push(userMessage)
        this.inputText = ''
        
        // 添加 AI 响应（来自缓存）
        this.messages.push(aiMessage)
        
        // 添加到历史记录
        this.addToHistory(messageText, cachedResult.result, cachedResult.result.chart_type)
        
        // 不显示加载状态，因为是缓存结果
        return
      }
      
      // 添加用户消息
      const userMessage: Message = {
        id: `msg_${Date.now()}`,
        role: 'user',
        content: messageText,
        timestamp: new Date()
      }
      this.messages.push(userMessage)
      this.inputText = ''
      
      // 显示加载状态
      uiStore.setLoading(true, '正在分析您的问题...')
      
      try {
        const response = await service.post('/query', {
          text: messageText,
          session_id: this.currentSessionId,
          data_source_id: this.currentDataSource,
          mode: this.chatMode
        })
        
        const data = response.data || response
        
        // 添加 AI 响应
        const aiMessage: Message = {
          id: `msg_${Date.now()}_ai`,
          role: 'assistant',
          content: data.result?.explanation || '查询完成',
          timestamp: new Date(),
          chartType: data.result?.chart_type,
          chartData: data.result?.data,
          actions: [
            { type: 'refresh', label: '刷新', handler: () => this.sendMessage(messageText) },
            { type: 'like', label: '点赞', handler: () => console.log('liked') },
            { type: 'dislike', label: '点踩', handler: () => console.log('disliked') }
          ]
        }
        this.messages.push(aiMessage)
        
        // 添加到历史记录
        this.addToHistory(messageText, data.result, data.result?.chart_type)
        
        // 缓存查询结果
        this.queryCache.set(cacheKey, { result: data.result, timestamp: new Date() })
        
      } catch (error) {
        uiStore.showToast((error as Error).message, 'error')
        
        // 添加错误消息
        const errorMessage: Message = {
          id: `msg_${Date.now()}_error`,
          role: 'assistant',
          content: `抱歉，处理您的请求时出现错误：${(error as Error).message}`,
          timestamp: new Date()
        }
        this.messages.push(errorMessage)
      } finally {
        uiStore.setLoading(false)
      }
    },
    
    clearMessages() {
      this.messages = []
    },
    
    // ========== 模式切换 ==========
    
    toggleChatMode() {
      this.chatMode = this.chatMode === 'query' ? 'report' : 'query'
    },
    
    setChatMode(mode: 'query' | 'report') {
      this.chatMode = mode
    },
    
    // ========== 数据源管理 ==========
    
    setDataSource(dataSourceId: string) {
      this.currentDataSource = dataSourceId
    },
    
    // ========== 历史记录 ==========
    
    async loadHistory() {
      const uiStore = useUIStore()
      try {
        const response = await service.get('/query/history')
        const data = response.data || response
        this.queryHistory = data.map((h: any) => ({
          ...h,
          createdAt: new Date(h.created_at)
        }))
      } catch (error) {
        uiStore.showToast((error as Error).message, 'error')
      }
    },
    
    addToHistory(queryText: string, result: any, chartType: string) {
      this.queryHistory.unshift({
        id: Date.now(),
        queryText,
        result,
        chartType,
        createdAt: new Date()
      })
      
      // 限制历史记录数量
      if (this.queryHistory.length > 50) {
        this.queryHistory = this.queryHistory.slice(0, 50)
      }
    },
    
    async clearHistory() {
      const uiStore = useUIStore()
      try {
        await service.delete('/query/history')
        
        this.queryHistory = []
        uiStore.showToast('历史记录已清空', 'success')
      } catch (error) {
        uiStore.showToast((error as Error).message, 'error')
      }
    },
    
    // ========== 推荐问题 ==========
    
    selectRecommendedQuestion(question: string) {
      this.inputText = question
      this.sendMessage()
    },
    
    // 清空查询缓存
    clearCache() {
      this.queryCache.clear()
    }
  }
})
