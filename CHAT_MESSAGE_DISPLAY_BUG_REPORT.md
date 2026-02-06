# Chat Message Display Bug Report

## 🐛 Problem Description

When the user sends a chat message "张三下了几单" by clicking the send button, the message does not appear on the screen. The interface remains in the welcome state showing recommended questions.

## 🔍 Root Cause Analysis

### Issue 1: Incorrect Store Property Access

**Location**: `frontend/src/views/Home.vue` line 383-386

```typescript
// ❌ WRONG: Accessing non-existent property
const messages = computed(() => {
  return chatStore.messages  // This property doesn't exist!
})
```

**Chat Store Structure** (`frontend/src/store/modules/chat.ts`):
- The store has `sessions` object containing multiple sessions
- Each session has a `messages` array
- The store provides a `currentMessages` getter that returns messages from the current session
- There is NO `messages` property at the root level

### Issue 2: Missing Session Initialization

**Location**: `frontend/src/views/Home.vue` onMounted hook

The code calls `chatStore.loadSessions()` and `chatStore.loadHistory()`, but these methods don't exist in the chat store. The store needs a current session to be created before messages can be added.

### Issue 3: WebSocket Connection Status

The WebSocket service tries to connect to `ws://localhost:8000/api/stream/ws/default`, but:
1. Connection failures are silently caught (no error shown to user)
2. The send button doesn't check if WebSocket is connected
3. Messages are added to store even if WebSocket fails

## 📊 Browser Verification Results

### Test Environment
- Frontend: http://127.0.0.1:5173
- Backend: http://localhost:8000
- Database: Mock_data (MySQL)
- Test Data: User "张三" (ID: 1) with 2 orders

### Test Steps Performed
1. ✅ Opened browser at http://127.0.0.1:5173
2. ✅ Verified data source "mysql_test_source" is selected
3. ✅ Verified data tables "orders" and "users" are available
4. ✅ Entered message "张三下了几单" in input field
5. ✅ Clicked send button
6. ❌ **FAILED**: Message did not appear on screen

### Console Messages
```
msgid=385 [log] Loading sessions...
msgid=386 [log] Loading history...
msgid=387 [issue] No label associated with a form field (count: 4)
```

No WebSocket connection messages were logged, indicating the WebSocket may not have connected successfully.

### Network Requests
- No WebSocket connection request was observed
- No `/api/stream/ws/default` connection in network tab
- Only HTTP requests for data sources and tables were made

## 🔧 Required Fixes

### Fix 1: Correct Message Access in Home.vue

```typescript
// ✅ CORRECT: Use the currentMessages getter
const messages = computed(() => {
  return chatStore.currentMessages
})
```

### Fix 2: Ensure Session is Created

```typescript
onMounted(() => {
  // Create a session if none exists
  if (!chatStore.currentSessionId) {
    chatStore.createSession('新对话')
  }
  
  // Load data sources
  dataPrepStore.loadDataSources()
  
  // ... rest of initialization
})
```

### Fix 3: Add WebSocket Connection Feedback

```typescript
// In sendMessage function
const sendMessage = async () => {
  if (!canSend.value) return
  
  // Check WebSocket connection
  if (!websocketService.isConnected()) {
    ElMessage.warning('WebSocket 未连接，正在尝试重新连接...')
    try {
      await websocketService.connect()
    } catch (error) {
      ElMessage.error('无法连接到服务器，请检查后端服务是否运行')
      return
    }
  }
  
  // ... rest of send logic
}
```

### Fix 4: Remove Non-existent Store Methods

Remove these calls from onMounted:
```typescript
// ❌ These methods don't exist
chatStore.loadSessions()
chatStore.loadHistory()
```

## 📝 Implementation Priority

1. **HIGH**: Fix message access (Fix 1) - This is the primary cause
2. **HIGH**: Ensure session creation (Fix 2) - Required for messages to work
3. **MEDIUM**: Add WebSocket feedback (Fix 3) - Improves user experience
4. **LOW**: Remove non-existent methods (Fix 4) - Cleanup

## ✅ Verification Steps

After implementing fixes:

1. Open browser at http://127.0.0.1:5173
2. Verify welcome screen shows
3. Select data source and tables
4. Enter message "张三下了几单"
5. Click send button
6. **Expected**: Message appears in chat area
7. **Expected**: Welcome screen is hidden
8. **Expected**: WebSocket sends query to backend
9. **Expected**: AI response appears (if backend is working)

## 🎯 Success Criteria

- ✅ User message appears immediately after clicking send
- ✅ Welcome screen is hidden when messages exist
- ✅ WebSocket connection status is visible to user
- ✅ Error messages are shown if connection fails
- ✅ Chat interface is functional end-to-end

## 📸 Screenshots

- `chat_send_no_response.png`: Shows the state after clicking send - no message visible

## 🔗 Related Files

- `frontend/src/views/Home.vue` - Main chat interface
- `frontend/src/store/modules/chat.ts` - Chat state management
- `frontend/src/services/websocketService.ts` - WebSocket communication
- `backend/src/api/websocket_stream_api.py` - Backend WebSocket endpoint
