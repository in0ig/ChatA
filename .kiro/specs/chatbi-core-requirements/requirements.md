# ChatBI 核心功能需求文档

## 项目概述

ChatBI 是一个智能数据分析对话系统，模仿腾讯云 ChatBI 的核心功能。用户通过自然语言提问，系统利用 AI 模型生成 SQL 查询，执行后返回数据结果和可视化图表。

## 术语表

- **ChatBI_System**: 智能数据分析对话系统
- **Qwen_Model**: 阿里云 Qwen 大语言模型
- **OpenAI_Model**: 本地 OpenAI 模型
- **Chat_Session**: 基于 chatId 的对话会话
- **Data_Dictionary**: 数据字典，包含表字段的业务含义
- **Knowledge_Base**: 知识库，包含业务规则和说明
- **Stream_Response**: 流式响应输出

## 需求分类

### 数据准备需求（P1 - 高优先级，ChatBI前置条件）

#### 需求 1: 数据源连接管理

**用户故事**: 作为数据管理员，我需要连接各种数据源，以便为 ChatBI 提供数据基础。

**验收标准**:
1. THE ChatBI_System SHALL 支持 MySQL 和 SQL Server 数据库连接
2. WHEN 配置数据源 THEN ChatBI_System SHALL 提供连接测试功能
3. WHEN 连接测试成功 THEN ChatBI_System SHALL 保存数据源配置
4. THE ChatBI_System SHALL 支持连接池管理和连接状态监控
5. WHEN 数据源连接失败 THEN ChatBI_System SHALL 提供详细的错误信息

#### 需求 2: 表结构同步

**用户故事**: 作为数据管理员，我需要同步数据库表结构，以便 ChatBI 了解可用的数据表和字段。

**验收标准**:
1. WHEN 连接到数据源 THEN ChatBI_System SHALL 自动发现所有可用表
2. WHEN 选择表进行同步 THEN ChatBI_System SHALL 获取完整的表结构信息
3. THE ChatBI_System SHALL 存储表名、字段名、字段类型、字段注释等信息
4. WHEN 表结构发生变化 THEN ChatBI_System SHALL 支持增量同步
5. THE ChatBI_System SHALL 维护表结构的版本历史

#### 需求 3: 数据字典管理

**用户故事**: 作为业务专家，我需要为数据表字段添加业务含义，以便 ChatBI 能够准确理解字段语义。

**验收标准**:
1. WHEN 表结构同步完成 THEN ChatBI_System SHALL 允许为字段添加业务描述
2. THE Data_Dictionary SHALL 包含字段的中文名称、业务含义、取值范围等信息
3. WHEN 创建数据字典 THEN ChatBI_System SHALL 支持字典项的层级管理
4. THE ChatBI_System SHALL 支持数据字典的导入导出功能
5. WHEN 生成 SQL 时 THEN Qwen_Model SHALL 参考 Data_Dictionary 理解字段含义

### 核心功能需求（P0 - 最高优先级）

#### 需求 4: 智能对话查询

**用户故事**: 作为业务分析师，我希望通过自然语言提问获得数据分析结果，以便快速获取业务洞察。

**验收标准**:
1. WHEN 用户输入自然语言问题 THEN ChatBI_System SHALL 进行意图识别（智能问数 vs 生成报告）
2. WHEN 意图识别完成 THEN ChatBI_System SHALL 进行智能选表，整合 Knowledge_Base、数据表结构和 Data_Dictionary
3. WHEN 智能选表完成 THEN ChatBI_System SHALL 进行意图澄清，确认用户的具体需求
4. WHEN 意图澄清确认 THEN ChatBI_System SHALL 调用 Qwen_Model 生成相应的 SQL 查询
5. WHEN SQL 生成完成 THEN ChatBI_System SHALL 执行 SQL 并返回查询结果
6. WHEN 查询结果返回 THEN ChatBI_System SHALL 根据意图判断生成相应的图表展示
7. THE ChatBI_System SHALL 采用流式输出方式显示生成过程和结果
8. WHEN 显示流式内容 THEN ChatBI_System SHALL 使用灰色文本显示生成过程，黑色文本显示最终结果

#### 需求 4.1: 意图识别

**用户故事**: 作为系统，我需要准确识别用户的查询意图，以便提供合适的分析服务。

**验收标准**:
1. THE ChatBI_System SHALL 识别用户问题是"智能问数"还是"生成报告"类型
2. WHEN 识别为智能问数 THEN ChatBI_System SHALL 进入数据查询流程
3. WHEN 识别为生成报告 THEN ChatBI_System SHALL 进入报告生成流程
4. WHEN 意图不明确 THEN ChatBI_System SHALL 向用户询问澄清
5. THE ChatBI_System SHALL 记录意图识别的准确率用于模型优化

#### 需求 4.2: 智能选表

**用户故事**: 作为系统，我需要根据用户问题智能选择相关的数据表，以便生成准确的查询。

**验收标准**:
1. WHEN 进行智能选表 THEN ChatBI_System SHALL 整合 Knowledge_Base 中的业务规则
2. WHEN 进行智能选表 THEN ChatBI_System SHALL 分析所有可用数据表的结构信息
3. WHEN 进行智能选表 THEN ChatBI_System SHALL 参考 Data_Dictionary 中的字段业务含义
4. THE ChatBI_System SHALL 根据用户问题的关键词匹配相关表和字段
5. THE ChatBI_System SHALL 输出候选表列表及选择理由

#### 需求 4.3: 意图澄清

**用户故事**: 作为用户，我希望系统能够确认我的具体需求，以确保查询结果符合预期。

**验收标准**:
1. WHEN 智能选表完成 THEN ChatBI_System SHALL 向用户展示理解的查询意图
2. THE ChatBI_System SHALL 显示选择的数据表和相关字段
3. THE ChatBI_System SHALL 询问用户是否需要调整查询范围或条件
4. WHEN 用户确认意图 THEN ChatBI_System SHALL 继续 SQL 生成流程
5. WHEN 用户要求修改 THEN ChatBI_System SHALL 重新进行智能选表

#### 需求 5: 多轮对话管理

**用户故事**: 作为用户，我希望能够进行多轮对话，系统能够理解上下文，以便进行深入的数据分析。

**验收标准**:
1. WHEN 用户开始新对话 THEN ChatBI_System SHALL 创建唯一的 Chat_Session
2. WHEN 用户在同一会话中继续提问 THEN ChatBI_System SHALL 维护对话上下文
3. WHEN 需要上下文整合 THEN ChatBI_System SHALL 对对话历史进行 summary 处理
4. THE ChatBI_System SHALL 支持基于 chatId 的会话管理
5. WHEN 会话超过一定长度 THEN ChatBI_System SHALL 自动进行上下文压缩

#### 需求 6: 本地数据追问

**用户故事**: 作为用户，我希望对查询结果进行进一步追问，且数据不会发送到云端，以确保数据安全。

**验收标准**:
1. WHEN 用户对查询结果进行追问 THEN ChatBI_System SHALL 调用本地 OpenAI_Model 处理
2. THE ChatBI_System SHALL NOT 将实际数据发送给云端 Qwen_Model
3. WHEN 处理本地追问 THEN ChatBI_System SHALL 仅使用查询结果数据和用户问题
4. THE OpenAI_Model SHALL 基于结果数据生成分析和回答
5. WHEN 本地追问完成 THEN ChatBI_System SHALL 以流式方式返回分析结果

### 技术架构需求（P1 - 高优先级）

#### 需求 7: 流式响应架构

**用户故事**: 作为用户，我希望看到 AI 思考和生成的过程，以便了解分析的逻辑。

**验收标准**:
1. THE ChatBI_System SHALL 实现 WebSocket 或 Server-Sent Events 进行流式通信
2. WHEN AI 模型生成内容 THEN ChatBI_System SHALL 实时推送生成进度
3. THE Stream_Response SHALL 区分思考过程（灰色）和最终结果（黑色）
4. WHEN 流式传输中断 THEN ChatBI_System SHALL 支持断点续传
5. THE ChatBI_System SHALL 控制流式输出的速度以提升用户体验

#### 需求 8: AI 模型集成

**用户故事**: 作为系统架构师，我需要集成云端和本地 AI 模型，以实现不同场景的智能分析。

**验收标准**:
1. THE ChatBI_System SHALL 集成阿里云 Qwen 模型进行 SQL 生成
2. THE ChatBI_System SHALL 集成本地 OpenAI 模型进行数据追问
3. THE ChatBI_System SHALL 将 AI 对话使用的 prompt 统一管理在配置文件中
4. WHEN 调用 Qwen_Model 时 THEN ChatBI_System SHALL 传递用户问题、表结构、Data_Dictionary 和 Knowledge_Base 内容
5. WHEN 调用 OpenAI_Model 时 THEN ChatBI_System SHALL 仅传递查询结果和用户追问
6. THE ChatBI_System SHALL 实现模型调用的错误处理和重试机制

### 用户界面需求（P2 - 中优先级）

#### 需求 9: 对话界面优化

**用户故事**: 作为用户，我需要一个简洁的对话界面，专注于与 ChatBI 进行数据分析交互。

**验收标准**:
1. THE ChatBI_System SHALL 提供类似聊天应用的对话界面
2. WHEN 显示 AI 响应 THEN ChatBI_System SHALL 区分思考过程和最终结果的视觉样式
3. THE ChatBI_System SHALL 移除当前页面展示的推荐问题功能
4. WHEN 生成图表 THEN ChatBI_System SHALL 在对话中嵌入可交互的图表组件
5. THE ChatBI_System SHALL 支持对话历史的搜索和导出

#### 需求 10: 图表可视化

**用户故事**: 作为业务分析师，我希望查询结果能够自动生成合适的图表，以便直观理解数据。

**验收标准**:
1. WHEN 查询返回数值型数据 THEN ChatBI_System SHALL 根据数据特征选择合适的图表类型
2. THE ChatBI_System SHALL 支持柱状图、折线图、饼图、散点图等常见图表
3. WHEN 生成图表 THEN ChatBI_System SHALL 提供图表的交互功能（缩放、筛选等）
4. THE ChatBI_System SHALL 支持图表的导出（PNG、PDF 等格式）
5. WHEN 数据量较大 THEN ChatBI_System SHALL 自动进行数据聚合和采样

### 性能和安全需求（P2 - 中优先级）

#### 需求 11: 系统性能

**用户故事**: 作为用户，我希望系统响应迅速，以便高效完成数据分析工作。

**验收标准**:
1. WHEN 用户提交问题 THEN ChatBI_System SHALL 在 3 秒内开始流式响应
2. WHEN 执行 SQL 查询 THEN ChatBI_System SHALL 在 10 秒内返回结果（数据量 < 10万行）
3. THE ChatBI_System SHALL 支持查询结果的缓存机制
4. WHEN 系统负载较高 THEN ChatBI_System SHALL 实现请求队列和限流
5. THE ChatBI_System SHALL 监控和记录系统性能指标

#### 需求 12: 数据安全

**用户故事**: 作为企业用户，我需要确保数据安全，敏感数据不会泄露到外部。

**验收标准**:
1. THE ChatBI_System SHALL 确保实际数据不会发送给云端 Qwen_Model
2. WHEN 调用云端模型 THEN ChatBI_System SHALL 仅发送表结构元数据和业务问题
3. THE ChatBI_System SHALL 实现用户身份认证和权限控制
4. WHEN 处理敏感查询 THEN ChatBI_System SHALL 记录审计日志
5. THE ChatBI_System SHALL 支持数据脱敏和字段级权限控制

## 需求优先级总结

### P1 (高优先级) - 数据准备基础（ChatBI前置条件）
- 需求 1: 数据源连接管理
- 需求 2: 表结构同步
- 需求 3: 数据字典管理
- 需求 7: 流式响应架构
- 需求 8: AI 模型集成

### P0 (最高优先级) - 核心ChatBI功能
- 需求 4: 智能对话查询
  - 需求 4.1: 意图识别
  - 需求 4.2: 智能选表  
  - 需求 4.3: 意图澄清
- 需求 5: 多轮对话管理  
- 需求 6: 本地数据追问

### P2 (中优先级) - 用户体验
- 需求 9: 对话界面设计
- 需求 10: 图表可视化
- 需求 11: 系统性能
- 需求 12: 数据安全

## 实施建议

### 模块化开发路径

按照以下顺序完成每个模块的**完整实现**（前端+后端+测试）：

#### 第一阶段：数据源模块（P1优先级）
- 完成数据源的所有功能：MySQL 和 SQL Server 连接、配置、测试
- 包含完整的前端界面、后端API、数据库设计、单元测试、集成测试
- 验收标准：数据源模块独立可用，所有测试通过

#### 第二阶段：数据表模块（P1优先级）  
- 基于完成的数据源模块，实现表结构同步功能
- 包含表发现、结构同步、版本管理等完整功能
- 验收标准：能够完整同步和管理数据库表结构

#### 第三阶段：数据字典模块（P1优先级）
- 基于完成的数据表模块，实现数据字典管理
- 包含字典创建、字段映射、业务含义管理等功能
- 验收标准：为所有表字段提供完整的业务语义

#### 第四阶段：流式对话模块（P0优先级）
- 实现核心ChatBI功能：意图识别、智能选表、意图澄清
- 实现AI对话、SQL生成、流式响应
- 集成前面完成的数据基础模块（知识库、数据表结构、数据字典）
- 验收标准：用户可以通过自然语言查询数据，系统能够准确理解意图并选择合适的表

#### 第五阶段：多轮对话和本地追问（P0优先级）
- 实现上下文管理和本地OpenAI模型集成
- 完善对话体验和数据安全
- 验收标准：支持复杂的多轮数据分析对话

#### 第六阶段：图表可视化和界面优化（P2优先级）
- 实现图表自动生成和界面优化
- 移除推荐问题，优化用户体验
- 验收标准：提供完整的数据可视化能力

## 验收标准

### 功能验收
- 所有 P0 和 P1 优先级需求必须 100% 实现
- 核心对话流程端到端测试通过
- 数据安全要求严格执行

### 性能验收  
- 流式响应延迟 < 3 秒
- SQL 查询响应时间 < 10 秒
- 系统并发支持 > 100 用户

### 用户验收
- 用户能够通过自然语言完成常见数据分析任务
- 多轮对话体验流畅自然
- 图表展示直观准确