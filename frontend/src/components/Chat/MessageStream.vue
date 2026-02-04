<template>
  <div class="message-stream">
    <!-- 欢迎语和推荐问题（仅在无消息时显示） -->
    <div v-if="messages.length === 0" class="welcome-container">
      <div class="welcome-message">
        欢迎使用 ChatBI！我是您的智能数据分析助手，可以通过自然语言查询数据。
      </div>
      
      <div class="recommended-questions">
        <span class="label">推荐问题：</span>
        <div class="chips">
          <button 
            v-for="(question, index) in recommendedQuestions" 
            :key="index"
            class="chip"
            @click="selectRecommendedQuestion(question)"
          >
            {{ question }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 消息列表 -->
    <div class="messages-container">
      <div 
        v-for="message in messages" 
        :key="message.id"
        :class="['message', message.role === 'user' ? 'message-user' : 'message-assistant']"
      >
        <!-- 用户消息 -->
        <div v-if="message.role === 'user'" class="user-message">
          <div class="message-content">
            {{ message.content }}
          </div>
        </div>
        
        <!-- AI 消息 -->
        <div v-else class="ai-message">
          <div class="message-content">
            {{ message.content }}
          </div>
          
          <!-- 操作按钮 -->
          <div class="message-actions">
            <button 
              v-for="action in message.actions || []" 
              :key="action.type"
              class="action-btn"
              @click="action.handler"
            >
              {{ action.label }}
            </button>
          </div>
          
          <!-- 图表显示 -->
          <div v-if="message.chartType && message.chartData" class="chart-container">
            {{ message.chartType }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- 清空会话按钮 -->
    <div class="clear-session-container" v-if="messages.length > 0">
      <button class="clear-session-btn" @click="clearMessages">清空会话</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useChatStore } from '@/store/modules/chat'

const chatStore = useChatStore()

// 从 store 获取数据
const messages = computed(() => chatStore.messages)
const recommendedQuestions = computed(() => chatStore.recommendedQuestions)

// 方法绑定
const selectRecommendedQuestion = (question: string) => {
  chatStore.selectRecommendedQuestion(question)
}

const clearMessages = () => {
  chatStore.clearMessages()
}
</script>

<style scoped>
.message-stream {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow-y: auto;
  background-color: #f5f5f5;
}

.welcome-container {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.welcome-message {
  font-size: 16px;
  margin-bottom: 20px;
  line-height: 1.6;
}

.recommended-questions {
  margin-top: 20px;
}

.recommended-questions .label {
  display: block;
  margin-bottom: 10px;
  color: #888;
  font-size: 14px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.chip {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
  color: #1890ff;
  border-radius: 20px;
  padding: 6px 12px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.chip:hover {
  background-color: #91d5ff;
  color: white;
}

.messages-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.message {
  display: flex;
  max-width: 80%;
}

.user-message {
  margin-left: auto;
}

.ai-message {
  margin-right: auto;
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.user-message .message-content {
  background-color: #e6f7ff;
  color: #1890ff;
}

.ai-message .message-content {
  background-color: white;
  color: #333;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.message-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  justify-content: flex-end;
}

.action-btn {
  background-color: transparent;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  padding: 4px 10px;
  font-size: 12px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background-color: #f5f5f5;
}

.clear-session-container {
  text-align: center;
  padding: 10px 0;
}

.clear-session-btn {
  background-color: transparent;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 13px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-session-btn:hover {
  background-color: #f5f5f5;
}

.chart-container {
  margin-top: 10px;
  padding: 10px;
  background-color: #f8f9fa;
  border: 1px dashed #dee2e6;
  border-radius: 8px;
  font-size: 12px;
  color: #666;
  text-align: center;
}
</style>