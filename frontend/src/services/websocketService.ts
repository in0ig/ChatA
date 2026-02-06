/**
 * WebSocket 流式通信服务
 */
import type { WSMessage } from '@/types/chat'

export class WebSocketService {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3 // 减少重连次数
  private reconnectDelay = 2000 // 增加重连延迟
  private messageHandlers: Set<(message: WSMessage) => void> = new Set()
  private connectionHandlers: Set<(connected: boolean) => void> = new Set()
  private errorHandlers: Set<(error: Error) => void> = new Set()

  constructor(url: string) {
    this.url = url
  }

  // 连接 WebSocket
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.reconnectAttempts = 0
          this.notifyConnectionHandlers(true)
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data)
            this.notifyMessageHandlers(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onerror = (event) => {
          console.warn('WebSocket error:', event)
          const error = new Error('WebSocket connection error')
          this.notifyErrorHandlers(error)
          reject(error)
        }

        this.ws.onclose = () => {
          console.log('WebSocket disconnected')
          this.notifyConnectionHandlers(false)
          this.attemptReconnect()
        }
      } catch (error) {
        reject(error)
      }
    })
  }

  // 断开连接
  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  // 发送消息
  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      throw new Error('WebSocket is not connected')
    }
  }

  // 尝试重连
  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`尝试重连 WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
      
      setTimeout(() => {
        this.connect().catch(error => {
          console.warn('WebSocket 重连失败:', error)
        })
      }, this.reconnectDelay * this.reconnectAttempts)
    } else {
      console.warn('WebSocket 达到最大重连次数,停止重连')
      // 不再抛出错误,避免控制台噪音
    }
  }

  // 注册消息处理器
  onMessage(handler: (message: WSMessage) => void) {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  // 注册连接状态处理器
  onConnection(handler: (connected: boolean) => void) {
    this.connectionHandlers.add(handler)
    return () => this.connectionHandlers.delete(handler)
  }

  // 注册错误处理器
  onError(handler: (error: Error) => void) {
    this.errorHandlers.add(handler)
    return () => this.errorHandlers.delete(handler)
  }

  // 通知消息处理器
  private notifyMessageHandlers(message: WSMessage) {
    this.messageHandlers.forEach(handler => handler(message))
  }

  // 通知连接状态处理器
  private notifyConnectionHandlers(connected: boolean) {
    this.connectionHandlers.forEach(handler => handler(connected))
  }

  // 通知错误处理器
  private notifyErrorHandlers(error: Error) {
    this.errorHandlers.forEach(handler => handler(error))
  }

  // 获取连接状态
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

// 创建单例实例
// 注意：后端 WebSocket 端点需要 session_id，这里使用默认值
// 实际使用时应该从 chat store 获取当前 session_id
const wsBaseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/stream/ws/default'
export const websocketService = new WebSocketService(wsBaseUrl)
