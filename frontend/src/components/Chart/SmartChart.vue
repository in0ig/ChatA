<template>
  <div class="smart-chart-container" ref="chartContainer">
    <!-- 图表推荐提示 -->
    <div class="chart-recommendation" v-if="chartRecommendation && showToolbar">
      <el-alert
        :title="`推荐使用${getChartTypeLabel(currentChartType)}`"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          {{ chartRecommendation }}
        </template>
      </el-alert>
    </div>

    <!-- 图表工具栏 -->
    <div class="chart-toolbar" v-if="showToolbar">
      <el-button-group>
        <el-button
          v-for="chartType in availableChartTypes"
          :key="chartType"
          :type="currentChartType === chartType ? 'primary' : 'default'"
          size="small"
          @click="changeChartType(chartType)"
        >
          {{ getChartTypeLabel(chartType) }}
        </el-button>
      </el-button-group>

      <div class="chart-actions">
        <el-dropdown @command="handleExport" v-if="exportable" trigger="click">
          <el-button type="text" size="small">
            导出 <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">PNG图片</el-dropdown-item>
              <el-dropdown-item command="jpg">JPG图片</el-dropdown-item>
              <el-dropdown-item command="pdf">PDF文档</el-dropdown-item>
              <el-dropdown-item command="svg">SVG矢量图</el-dropdown-item>
              <el-dropdown-item command="excel">Excel数据</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-button type="text" size="small" @click="showSaveDialog = true">
          保存配置
        </el-button>

        <el-button type="text" size="small" @click="showShareDialog = true">
          分享
        </el-button>
      </div>
    </div>

    <!-- 图表容器 -->
    <div
      ref="chartElement"
      class="chart-element"
      :style="{ height: chartHeight }"
    ></div>

    <!-- 保存配置对话框 -->
    <el-dialog
      v-model="showSaveDialog"
      title="保存图表配置"
      width="500px"
    >
      <el-form :model="saveForm" label-width="100px">
        <el-form-item label="配置名称">
          <el-input v-model="saveForm.name" placeholder="请输入配置名称" />
        </el-form-item>
        <el-form-item label="保存为模板">
          <el-switch v-model="saveForm.asTemplate" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveConfig">保存</el-button>
      </template>
    </el-dialog>

    <!-- 分享对话框 -->
    <el-dialog
      v-model="showShareDialog"
      title="分享图表"
      width="600px"
    >
      <el-tabs v-model="shareTabActive">
        <el-tab-pane label="分享链接" name="link">
          <div class="share-content">
            <el-input
              v-model="shareLink"
              readonly
              placeholder="生成分享链接..."
            >
              <template #append>
                <el-button @click="copyShareLink">复制</el-button>
              </template>
            </el-input>
            <div class="share-options">
              <el-form label-width="100px" size="small">
                <el-form-item label="有效期">
                  <el-select v-model="shareOptions.expiresInDays">
                    <el-option label="永久" :value="0" />
                    <el-option label="7天" :value="7" />
                    <el-option label="30天" :value="30" />
                    <el-option label="90天" :value="90" />
                  </el-select>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="嵌入代码" name="embed">
          <div class="share-content">
            <el-input
              v-model="embedCode"
              type="textarea"
              :rows="6"
              readonly
              placeholder="生成嵌入代码..."
            />
            <el-button @click="copyEmbedCode" style="margin-top: 10px">
              复制代码
            </el-button>
          </div>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="showShareDialog = false">关闭</el-button>
        <el-button type="primary" @click="generateShare">生成</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import type { ECharts, EChartsOption } from 'echarts'
import { ArrowDown } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { SmartChartProps, ChartType, ChartData, ExportFormat, ChartConfig } from '@/types/chart'
import { ChartTypeSelector } from '@/utils/chartTypeSelector'
import { chartExportService } from '@/services/chartExportService'
import { chartConfigService } from '@/services/chartConfigService'
import { chartShareService } from '@/services/chartShareService'
import { chartInteractionService } from '@/services/chartInteractionService'
import { chartThemeService } from '@/services/chartThemeService'
import { chartAnimationService } from '@/services/chartAnimationService'
import { chartStreamingService } from '@/services/chartStreamingService'
import type { ContextMenuItem, DataPointSelection } from '@/services/chartInteractionService'
import type { StreamingConfig } from '@/services/chartStreamingService'

const props = withDefaults(defineProps<SmartChartProps>(), {
  type: 'auto',
  theme: 'light',
  responsive: true,
  exportable: true,
  options: () => ({})
})

const chartContainer = ref<HTMLElement>()
const chartElement = ref<HTMLElement>()
let chartInstance: ECharts | null = null

const currentChartType = ref<ChartType>('bar')
const chartTypeSelector = new ChartTypeSelector()
const isLoadingChartType = ref(false)
const chartRecommendation = ref<string>('')

// 流式渲染状态
const isStreaming = ref(false)
const streamedData = ref<any[]>([])
const streamProgress = ref(0)
const chartId = `chart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

// 保存和分享相关状态
const showSaveDialog = ref(false)
const showShareDialog = ref(false)
const shareTabActive = ref('link')
const shareLink = ref('')
const embedCode = ref('')
const saveForm = ref({
  name: '',
  asTemplate: false
})
const shareOptions = ref({
  expiresInDays: 0
})

// 计算属性
const availableChartTypes = computed(() => {
  return chartTypeSelector.getAvailableTypes(props.data)
})

const chartHeight = computed(() => {
  return props.options?.height || (props.responsive ? '400px' : '300px')
})

const showToolbar = computed(() => {
  return props.options?.showToolbar !== false
})

// 监听数据变化
watch(() => props.data, async (newData, oldData) => {
  if (!newData) return

  // 检查是否需要流式渲染
  const shouldStream = chartStreamingService.shouldUseStreaming(newData.rows.length)
  
  if (shouldStream && props.options?.enableStreamingUpdate !== false) {
    // 流式渲染模式
    await renderChartStreaming(newData)
  } else {
    // 检测是否为增量更新
    const isIncremental = oldData && 
      newData.columns.length === oldData.columns.length &&
      newData.rows.length > oldData.rows.length
    
    if (isIncremental && props.options?.enableIncrementalUpdate) {
      // 增量更新模式
      await updateChartIncremental(newData, oldData)
    } else {
      // 完全更新模式
      if (props.type === 'auto') {
        await selectChartTypeWithAI(newData)
      }
      updateChart()
    }
  }
}, { deep: true })

watch(() => props.type, (newType) => {
  if (newType !== 'auto') {
    currentChartType.value = newType as ChartType
    chartRecommendation.value = ''
    updateChart()
  }
})

watch(() => props.theme, () => {
  if (chartInstance) {
    chartInstance.dispose()
    initChart()
  }
})

// 生命周期
onMounted(() => {
  initChart()
})

onUnmounted(() => {
  cleanup()
})

// 方法
async function initChart() {
  if (!chartElement.value) return

  // 注册自定义主题
  const themeConfig = chartThemeService.generateEChartsTheme(props.theme || 'light')
  echarts.registerTheme(props.theme || 'light', themeConfig)

  chartInstance = echarts.init(chartElement.value, props.theme)

  // 自动选择图表类型
  if (props.type === 'auto') {
    await selectChartTypeWithAI(props.data)
  } else {
    currentChartType.value = props.type as ChartType
  }

  updateChart()

  // 集成交互服务
  if (chartInstance) {
    initInteractionFeatures(chartInstance)
  }

  // 响应式处理
  if (props.responsive) {
    window.addEventListener('resize', handleResize)
  }
}

/**
 * 初始化交互功能
 */
function initInteractionFeatures(chart: ECharts) {
  // 启用上下文菜单
  if (props.options?.enableContextMenu) {
    const menuItems: ContextMenuItem[] = [
      {
        label: '导出为PNG',
        action: () => handleExport('png')
      },
      {
        label: '导出为Excel',
        action: () => handleExport('excel')
      },
      {
        label: '复制数据',
        action: (data: any) => {
          console.log('Copy data:', data)
          ElMessage.success('数据已复制')
        }
      }
    ]
    chartInteractionService.enableContextMenu(chart, menuItems)
  }

  // 启用数据点选择
  if (props.options?.enableDataPointSelection) {
    chartInteractionService.enableDataPointSelection(
      chart,
      (selections: DataPointSelection[]) => {
        console.log('Selected data points:', selections)
        ElMessage.info(`已选择 ${selections.length} 个数据点`)
      }
    )
  }

  // 启用钻取功能
  if (props.options?.enableDrillDown) {
    chartInteractionService.enableDrillDown(chart, {
      enabled: true,
      onDrillDown: (data: DataPointSelection) => {
        console.log('Drill down:', data)
        ElMessage.info(`钻取到: ${data.name}`)
      },
      onDrillUp: () => {
        console.log('Drill up')
        ElMessage.info('返回上一层')
      }
    })
  }

  // 启用图表联动
  if (props.options?.enableChartLinkage && props.options?.linkageGroup) {
    chartInteractionService.enableChartLinkage(chart, {
      group: props.options.linkageGroup,
      enabled: true
    })
  }
}

/**
 * 使用AI选择图表类型
 */
async function selectChartTypeWithAI(data: ChartData) {
  isLoadingChartType.value = true
  
  try {
    // 尝试使用AI选择
    const result = await chartTypeSelector.selectOptimalChartAsync(data)
    currentChartType.value = result.primary.type
    chartRecommendation.value = result.primary.reason
    
    console.log('AI Chart Selection:', {
      primary: result.primary,
      alternatives: result.alternatives,
      dataAnalysis: result.dataAnalysis
    })
  } catch (error) {
    console.warn('Failed to select chart type with AI, using fallback:', error)
    // 降级到规则引擎
    currentChartType.value = chartTypeSelector.selectOptimalChart(data)
    chartRecommendation.value = ''
  } finally {
    isLoadingChartType.value = false
  }
}

function updateChart() {
  if (!chartInstance) return

  let dataToRender = props.data
  
  // 检查是否为大数据量，需要优化
  if (chartStreamingService.isLargeDataset(props.data.rows.length)) {
    // 应用大数据量优化
    const option = generateChartOption(currentChartType.value, dataToRender)
    const optimized = chartStreamingService.optimizeForLargeDataset(
      option,
      props.data.rows.length
    )
    
    chartInstance.setOption(optimized, true)
    
    ElMessage.info({
      message: `检测到大数据量(${props.data.rows.length}条)，已启用性能优化`,
      duration: 2000
    })
    return
  }

  let option = generateChartOption(currentChartType.value, dataToRender)
  
  // 应用动画配置
  if (props.options?.animationPreset) {
    const animConfig = chartAnimationService.getAnimationConfig(props.options.animationPreset)
    option = chartAnimationService.applyAnimation(option, animConfig)
  } else if (props.options?.animationDuration || props.options?.animationEasing) {
    option = chartAnimationService.applyAnimation(option, {
      enabled: props.options?.animation !== false,
      duration: props.options?.animationDuration || 1000,
      easing: props.options?.animationEasing || 'cubicOut'
    })
  }

  chartInstance.setOption(option, true)
}

/**
 * 增量更新图表数据
 */
async function updateChartIncremental(newData: ChartData, oldData: ChartData) {
  if (!chartInstance) return

  // 显示加载动画
  if (props.options?.showLoadingOnUpdate) {
    const loadingConfig = chartStreamingService.getLoadingAnimation()
    chartInstance.showLoading('default', loadingConfig)
  }

  // 计算新增的数据
  const newRows = newData.rows.slice(oldData.rows.length)
  
  // 使用增量更新服务
  const mergedRows = chartStreamingService.incrementalUpdate(
    chartId,
    newRows,
    streamedData.value.length > 0 ? streamedData.value : oldData.rows
  )
  
  streamedData.value = mergedRows

  // 构建新的数据对象
  const updatedData: ChartData = {
    ...newData,
    rows: mergedRows
  }

  // 更新图表
  const option = generateChartOption(currentChartType.value, updatedData)
  
  // 应用平滑动画
  const animatedOption = chartAnimationService.applyAnimation(option, {
    enabled: true,
    duration: 500,
    easing: 'cubicOut'
  })

  chartInstance.setOption(animatedOption, false)

  // 隐藏加载动画
  if (props.options?.showLoadingOnUpdate) {
    chartInstance.hideLoading()
  }

  ElMessage.success(`新增 ${newRows.length} 条数据`)
}

/**
 * 流式渲染图表
 */
async function renderChartStreaming(data: ChartData) {
  if (!chartInstance) return

  isStreaming.value = true
  streamProgress.value = 0
  streamedData.value = []

  // 显示加载动画
  const loadingConfig = chartStreamingService.getLoadingAnimation()
  chartInstance.showLoading('default', loadingConfig)

  try {
    // 使用流式渲染服务
    await chartStreamingService.streamData(
      chartId,
      data.rows,
      (batch, accumulatedData) => {
        // 更新进度
        const state = chartStreamingService.getState()
        streamProgress.value = state.progress
        streamedData.value = accumulatedData

        // 构建当前批次的数据对象
        const currentData: ChartData = {
          ...data,
          rows: accumulatedData
        }

        // 更新图表
        const option = generateChartOption(currentChartType.value, currentData)
        chartInstance?.setOption(option, false)
      },
      () => {
        // 完成回调
        chartInstance?.hideLoading()
        isStreaming.value = false
        streamProgress.value = 100
        ElMessage.success('数据加载完成')
      }
    )
  } catch (error) {
    console.error('Streaming render failed:', error)
    chartInstance.hideLoading()
    isStreaming.value = false
    ElMessage.error('数据加载失败')
  }
}

function generateChartOption(type: ChartType, data: ChartData): EChartsOption {
  const baseOption: EChartsOption = {
    title: {
      text: data.title || '',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      confine: true,
      backgroundColor: 'rgba(50, 50, 50, 0.9)',
      borderColor: '#333',
      borderWidth: 0,
      textStyle: {
        color: '#fff',
        fontSize: 12
      },
      padding: [8, 12],
      formatter: (params: any) => {
        if (Array.isArray(params)) {
          let result = `<div style="font-weight: bold; margin-bottom: 4px;">${params[0].axisValue}</div>`
          params.forEach((param: any) => {
            result += `<div style="margin: 2px 0;">
              <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${param.color};margin-right:5px;"></span>
              ${param.seriesName}: <span style="font-weight: bold;">${param.value}</span>
            </div>`
          })
          return result
        }
        return params.name + ': ' + params.value
      }
    },
    legend: {
      show: props.options?.showLegend !== false,
      top: 'bottom',
      type: 'scroll',
      pageButtonItemGap: 5,
      pageButtonGap: 20,
      pageIconSize: 12,
      pageTextStyle: {
        color: '#666'
      },
      selectedMode: true // 启用图例点击切换
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    // 添加工具栏
    toolbox: {
      show: props.options?.showToolbox !== false,
      feature: {
        dataZoom: {
          yAxisIndex: 'none',
          title: {
            zoom: '区域缩放',
            back: '还原缩放'
          }
        },
        restore: {
          title: '还原'
        },
        saveAsImage: {
          title: '保存为图片',
          pixelRatio: 2
        }
      },
      right: '20px',
      top: '10px'
    },
    // 添加数据缩放组件
    dataZoom: props.options?.enableDataZoom !== false ? [
      {
        type: 'slider',
        show: data.rows.length > 20, // 数据量大时显示
        xAxisIndex: [0],
        start: 0,
        end: 100,
        height: 20,
        bottom: '5%',
        handleSize: '80%',
        handleStyle: {
          color: '#188df0'
        },
        textStyle: {
          color: '#666'
        },
        borderColor: '#ddd'
      },
      {
        type: 'inside',
        xAxisIndex: [0],
        start: 0,
        end: 100
      }
    ] : undefined
  }

  switch (type) {
    case 'bar':
      return generateBarChart(baseOption, data)
    case 'line':
      return generateLineChart(baseOption, data)
    case 'pie':
      return generatePieChart(baseOption, data)
    case 'scatter':
      return generateScatterChart(baseOption, data)
    case 'heatmap':
      return generateHeatmapChart(baseOption, data)
    case 'radar':
      return generateRadarChart(baseOption, data)
    default:
      return generateBarChart(baseOption, data)
  }
}

function generateBarChart(baseOption: EChartsOption, data: ChartData): EChartsOption {
  return {
    ...baseOption,
    xAxis: {
      type: 'category',
      data: data.rows.map(row => row[0]),
      axisLabel: {
        rotate: data.rows.length > 10 ? 45 : 0,
        interval: 0
      }
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      type: 'bar',
      data: data.rows.map(row => row[1]),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ])
      },
      emphasis: {
        focus: 'series',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2378f7' },
            { offset: 0.7, color: '#2378f7' },
            { offset: 1, color: '#83bff6' }
          ]),
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      // 启用选中效果
      select: {
        itemStyle: {
          color: '#2378f7',
          borderColor: '#fff',
          borderWidth: 2
        }
      },
      selectedMode: 'single' // 单选模式
    }]
  }
}

function generateLineChart(baseOption: EChartsOption, data: ChartData): EChartsOption {
  return {
    ...baseOption,
    xAxis: {
      type: 'category',
      data: data.rows.map(row => row[0]),
      boundaryGap: false
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      type: 'line',
      data: data.rows.map(row => row[1]),
      smooth: true,
      lineStyle: {
        color: '#188df0',
        width: 2
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(24, 141, 240, 0.3)' },
          { offset: 1, color: 'rgba(24, 141, 240, 0.1)' }
        ])
      },
      emphasis: {
        focus: 'series',
        lineStyle: {
          width: 3
        }
      },
      // 数据点样式
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: {
        color: '#188df0',
        borderColor: '#fff',
        borderWidth: 2
      },
      // 悬停时数据点放大
      emphasis: {
        itemStyle: {
          color: '#2378f7',
          borderColor: '#fff',
          borderWidth: 3,
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        },
        scale: true,
        scaleSize: 12
      }
    }]
  }
}

function generatePieChart(baseOption: EChartsOption, data: ChartData): EChartsOption {
  return {
    ...baseOption,
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    series: [{
      name: data.columns[0] || '数据',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: true,
        formatter: '{b}: {d}%'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 14,
          fontWeight: 'bold'
        },
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      data: data.rows.map(row => ({
        name: row[0],
        value: row[1]
      }))
    }]
  }
}

function generateScatterChart(baseOption: EChartsOption, data: ChartData): EChartsOption {
  return {
    ...baseOption,
    xAxis: {
      type: 'value',
      name: data.columns[0] || 'X',
      nameLocation: 'middle',
      nameGap: 30
    },
    yAxis: {
      type: 'value',
      name: data.columns[1] || 'Y',
      nameLocation: 'middle',
      nameGap: 40
    },
    series: [{
      type: 'scatter',
      data: data.rows.map(row => [row[0], row[1]]),
      symbolSize: 10,
      itemStyle: {
        color: '#188df0',
        opacity: 0.7
      },
      emphasis: {
        itemStyle: {
          color: '#2378f7',
          opacity: 1,
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    }]
  }
}

function generateHeatmapChart(baseOption: EChartsOption, data: ChartData): EChartsOption {
  // 简化的热力图实现
  const xAxisData = [...new Set(data.rows.map(row => row[0]))]
  const yAxisData = [...new Set(data.rows.map(row => row[1]))]
  
  return {
    ...baseOption,
    tooltip: {
      position: 'top'
    },
    grid: {
      height: '50%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      splitArea: {
        show: true
      }
    },
    yAxis: {
      type: 'category',
      data: yAxisData,
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: Math.max(...data.rows.map(row => row[2] || 0)),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '15%'
    },
    series: [{
      type: 'heatmap',
      data: data.rows.map(row => [row[0], row[1], row[2] || 0]),
      label: {
        show: true
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }
}

function generateRadarChart(baseOption: EChartsOption, data: ChartData): EChartsOption {
  const indicators = data.columns.slice(1).map(col => ({ name: col, max: 100 }))
  
  return {
    ...baseOption,
    radar: {
      indicator: indicators
    },
    series: [{
      type: 'radar',
      data: data.rows.map(row => ({
        value: row.slice(1),
        name: row[0]
      })),
      areaStyle: {
        opacity: 0.3
      }
    }]
  }
}

function changeChartType(type: ChartType) {
  currentChartType.value = type
  updateChart()
}

function handleExport(format: ExportFormat) {
  if (!chartInstance) return

  try {
    if (format === 'pdf') {
      chartExportService.exportAsPDF(chartInstance, 'chart', {
        title: props.data.title
      })
    } else if (format === 'excel') {
      chartExportService.exportAsExcel(props.data, 'chart-data')
    } else {
      chartExportService.exportAsImage(chartInstance, format, 'chart')
    }
    ElMessage.success(`导出${format.toUpperCase()}成功`)
  } catch (error) {
    console.error('Export failed:', error)
    ElMessage.error('导出失败')
  }
}

function handleSaveConfig() {
  if (!saveForm.value.name) {
    ElMessage.warning('请输入配置名称')
    return
  }

  try {
    const config: ChartConfig = {
      name: saveForm.value.name,
      type: currentChartType.value,
      data: props.data,
      options: props.options || {},
      theme: props.theme || 'light'
    }

    if (saveForm.value.asTemplate) {
      const template = {
        id: `template_${Date.now()}`,
        name: saveForm.value.name,
        type: currentChartType.value,
        options: props.options || {},
        theme: props.theme || 'light'
      }
      chartConfigService.saveTemplate(template)
      ElMessage.success('模板保存成功')
    } else {
      const id = chartConfigService.saveConfig(config)
      ElMessage.success(`配置保存成功 (ID: ${id})`)
    }

    showSaveDialog.value = false
    saveForm.value.name = ''
    saveForm.value.asTemplate = false
  } catch (error) {
    console.error('Save config failed:', error)
    ElMessage.error('保存失败')
  }
}

function generateShare() {
  try {
    const config: ChartConfig = {
      name: props.data.title || '图表',
      type: currentChartType.value,
      data: props.data,
      options: props.options || {},
      theme: props.theme || 'light'
    }

    const shareConfig = chartShareService.generateShareLink(config, {
      expiresInDays: shareOptions.value.expiresInDays || undefined
    })

    shareLink.value = shareConfig.shareUrl
    embedCode.value = shareConfig.embedCode

    ElMessage.success('分享链接生成成功')
  } catch (error) {
    console.error('Generate share failed:', error)
    ElMessage.error('生成分享链接失败')
  }
}

async function copyShareLink() {
  const success = await chartShareService.copyToClipboard(shareLink.value)
  if (success) {
    ElMessage.success('分享链接已复制到剪贴板')
  } else {
    ElMessage.error('复制失败')
  }
}

async function copyEmbedCode() {
  const success = await chartShareService.copyToClipboard(embedCode.value)
  if (success) {
    ElMessage.success('嵌入代码已复制到剪贴板')
  } else {
    ElMessage.error('复制失败')
  }
}

function exportChart(format: ExportFormat) {
  handleExport(format)
}

function handleResize() {
  if (chartInstance) {
    chartInstance.resize()
  }
}

function cleanup() {
  if (props.responsive) {
    window.removeEventListener('resize', handleResize)
  }
  
  // 清理流式渲染资源
  chartStreamingService.cleanup(chartId)
  
  // 清理交互服务
  if (chartInstance && props.options?.linkageGroup) {
    chartInteractionService.disableChartLinkage(chartInstance, props.options.linkageGroup)
  }
  chartInteractionService.cleanup()
  
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
}

function getChartTypeLabel(type: ChartType): string {
  const labels: Record<ChartType, string> = {
    bar: '柱状图',
    line: '折线图',
    pie: '饼图',
    scatter: '散点图',
    heatmap: '热力图',
    radar: '雷达图'
  }
  return labels[type] || type
}
</script>

<style scoped>
.smart-chart-container {
  width: 100%;
  position: relative;
  background: #fff;
  border-radius: 4px;
  padding: 16px;
}

.chart-recommendation {
  margin-bottom: 12px;
}

.chart-recommendation :deep(.el-alert) {
  padding: 8px 12px;
}

.chart-recommendation :deep(.el-alert__title) {
  font-size: 14px;
  font-weight: 500;
}

.chart-recommendation :deep(.el-alert__description) {
  font-size: 12px;
  margin-top: 4px;
  color: #606266;
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e4e7ed;
}

.chart-element {
  width: 100%;
  min-height: 300px;
}

.chart-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.share-content {
  padding: 10px 0;
}

.share-options {
  margin-top: 20px;
}
</style>
