<template>
  <div class="ticket-list">
    <el-card class="filter-card">
      <div class="filter-bar">
        <el-form :inline="true" :model="filterForm">
          <el-form-item label="品牌">
            <el-select v-model="filterForm.brand" placeholder="全部品牌" clearable style="width: 150px">
              <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
            </el-select>
          </el-form-item>
          <el-form-item label="状态">
            <el-select v-model="filterForm.status" placeholder="全部状态" clearable style="width: 150px">
              <el-option v-for="s in statusOptions" :key="s.value" :label="s.label" :value="s.value" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="fetchTickets">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetFilter">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
        <el-button type="success" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          新增工单
        </el-button>
      </div>
    </el-card>

    <el-card class="table-card">
      <el-table :data="tickets" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="id" label="工单ID" width="80" />
        <el-table-column prop="brand" label="品牌" width="100">
          <template #default="{ row }">
            <el-tag :type="getBrandTagType(row.brand)">{{ row.brand }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="store_code" label="门店编号" width="120" />
        <el-table-column prop="complaint_type" label="投诉类型" width="120" />
        <el-table-column prop="handler" label="处理人" width="100" />
        <el-table-column prop="compensation_amount" label="补偿金额" width="100">
          <template #default="{ row }">
            <span v-if="row.compensation_amount > 0">¥{{ row.compensation_amount }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_closed" label="状态" width="130">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)" size="small">
              {{ getStatusName(row.status) }}
            </el-tag>
            <el-tooltip v-if="row.sla_hours_remaining !== null && row.status !== 'processing'" placement="top">
              <template #content>
                <div>剩余时间: {{ row.sla_hours_remaining }}小时</div>
                <div v-if="row.is_sla_breached" style="color: #f56c6c; font-weight: bold;">⚠️ 已超时!</div>
              </template>
              <span v-if="row.is_sla_breached" class="sla-badge sla-breached">
                SLA超时
              </span>
              <span v-else-if="row.sla_hours_remaining !== null" class="sla-badge" :class="row.sla_hours_remaining < 1 ? 'sla-warning' : ''">
                {{ row.sla_hours_remaining }}h
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="has_compensation" label="有补偿" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.has_compensation" type="primary">是</el-tag>
            <el-tag v-else type="info">否</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">
              <el-icon><View /></el-icon>
              详情
            </el-button>
            <el-button type="success" link @click="openEditDialog(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="danger" link @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="ticketFormRef"
        :model="ticketForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="品牌" prop="brand">
              <el-select v-model="ticketForm.brand" placeholder="请选择品牌" style="width: 100%">
                <el-option v-for="b in brands" :key="b" :label="b" :value="b" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="门店编号" prop="store_code">
              <el-input v-model="ticketForm.store_code" placeholder="请输入门店编号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="投诉类型" prop="complaint_type">
              <el-select v-model="ticketForm.complaint_type" placeholder="请选择投诉类型" style="width: 100%">
                <el-option v-for="t in complaintTypes" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="处理人" prop="handler">
              <el-input v-model="ticketForm.handler" placeholder="请输入处理人" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="是否补偿" prop="has_compensation">
          <el-switch v-model="ticketForm.has_compensation" />
        </el-form-item>

        <template v-if="ticketForm.has_compensation">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="补偿类型" prop="compensation_type">
                <el-select v-model="ticketForm.compensation_type" placeholder="请选择补偿类型" style="width: 100%">
                  <el-option v-for="t in compensationTypes" :key="t" :label="t" :value="t" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="补偿金额" prop="compensation_amount">
                <el-input-number v-model="ticketForm.compensation_amount" :min="0" :step="10" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
        </template>

        <el-form-item label="是否结案" prop="is_closed">
          <el-switch v-model="ticketForm.is_closed" />
        </el-form-item>

        <el-form-item v-if="ticketForm.is_closed" label="结案备注" prop="closing_remark">
          <el-input
            v-model="ticketForm.closing_remark"
            type="textarea"
            :rows="3"
            placeholder="请输入结案备注"
          />
        </el-form-item>

        <el-form-item v-if="isEditMode" label="图片附件">
          <el-upload
            :action="uploadUrl"
            :headers="uploadHeaders"
            list-type="picture-card"
            :file-list="imageFileList"
            :on-success="handleUploadSuccess"
            :before-upload="beforeUpload"
            multiple
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="upload-tip">支持 jpg、png、gif 等图片格式</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailVisible" title="工单详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="工单ID">{{ currentTicket.id }}</el-descriptions-item>
        <el-descriptions-item label="品牌">
          <el-tag :type="getBrandTagType(currentTicket.brand)">{{ currentTicket.brand }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="门店编号">{{ currentTicket.store_code }}</el-descriptions-item>
        <el-descriptions-item label="投诉类型">{{ currentTicket.complaint_type }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ currentTicket.handler }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusTagType(currentTicket.status)" size="small">
            {{ getStatusName(currentTicket.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="是否补偿">
          {{ currentTicket.has_compensation ? '是' : '否' }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentTicket.has_compensation" label="补偿类型">
          {{ currentTicket.compensation_type }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentTicket.has_compensation" label="补偿金额">
          ¥{{ currentTicket.compensation_amount }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentTicket.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDate(currentTicket.updated_at) }}</el-descriptions-item>
        <el-descriptions-item v-if="currentTicket.closing_remark" label="结案备注" :span="2">
          {{ currentTicket.closing_remark }}
        </el-descriptions-item>
        <el-descriptions-item v-if="currentTicket.rejected_reason" label="驳回原因" :span="2">
          {{ currentTicket.rejected_reason }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="status-actions" v-if="currentTicket.status !== 'closed'">
        <h4>状态流转</h4>
        <div class="action-buttons">
          <el-button 
            v-if="currentTicket.status === 'pending'" 
            type="primary" 
            @click="handleStatusTransition('accept')"
            :loading="transitioning"
          >
            受理
          </el-button>
          <el-button 
            v-if="currentTicket.status === 'pending' || currentTicket.status === 'review'" 
            type="warning" 
            @click="handleStatusTransition('process')"
            :loading="transitioning"
          >
            开始处理
          </el-button>
          <el-button 
            v-if="currentTicket.status === 'processing'" 
            type="primary" 
            @click="handleStatusTransition('review')"
            :loading="transitioning"
          >
            提交复核
          </el-button>
          <el-button 
            v-if="currentTicket.status === 'review'" 
            type="success" 
            @click="handleStatusTransition('close')"
            :loading="transitioning"
          >
            结案
          </el-button>
          <el-button 
            v-if="currentTicket.status === 'review'" 
            type="danger" 
            @click="showRejectDialog"
          >
            驳回
          </el-button>
        </div>
      </div>

      <div v-if="currentTicket.images && currentTicket.images.length > 0" class="detail-images">
        <h4>图片附件</h4>
        <div class="image-gallery">
          <el-image
            v-for="img in currentTicket.images"
            :key="img.id"
            :src="getImageUrl(img.file_path)"
            :preview-src-list="currentTicket.images.map(i => getImageUrl(i.file_path))"
            fit="cover"
            class="gallery-image"
          />
        </div>
      </div>

      <div class="operation-timeline" v-if="operationLogs.length > 0">
        <h4>操作时间线</h4>
        <div class="timeline-filter">
          <el-select v-model="logFilter" placeholder="筛选动作类型" clearable size="small" style="width: 150px;">
            <el-option v-for="(label, action) in actionLabels" :key="action" :label="label" :value="action" />
          </el-select>
        </div>
        <el-timeline>
          <el-timeline-item
            v-for="log in filteredLogs"
            :key="log.id"
            :timestamp="formatDate(log.created_at)"
            :type="getLogType(log.action)"
          >
            <div class="log-content">
              <strong>{{ actionLabels[log.action] || log.action }}</strong>
              <div class="log-detail">
                <span>操作人: {{ log.operator }}</span>
                <span v-if="log.client_ip">IP: {{ log.client_ip }}</span>
              </div>
              <div v-if="log.remark" class="log-remark">{{ log.remark }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </el-dialog>

    <el-dialog v-model="rejectDialogVisible" title="驳回工单" width="400px">
      <el-form :model="rejectForm" label-width="100px">
        <el-form-item label="驳回原因" required>
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请输入驳回原因（必填）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleReject" :loading="transitioning">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getTickets,
  createTicket,
  updateTicket,
  deleteTicket,
  transitionStatus,
  getOperationLogs,
  uploadImages,
  getBrands,
  getComplaintTypes,
  getCompensationTypes,
  getStatuses,
  getSlaConfig,
  getActions
} from '../utils/api'

const loading = ref(false)
const submitting = ref(false)
const transitioning = ref(false)
const tickets = ref([])
const brands = ref([])
const complaintTypes = ref([])
const compensationTypes = ref([])
const statusOptions = ref([])
const slaConfig = ref({})
const actionLabels = ref({})

const filterForm = reactive({
  brand: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  page_size: 10,
  total: 0
})

const dialogVisible = ref(false)
const detailVisible = ref(false)
const rejectDialogVisible = ref(false)
const isEditMode = ref(false)
const currentTicketId = ref(null)
const ticketFormRef = ref(null)
const imageFileList = ref([])

const operationLogs = ref([])
const logFilter = ref('')

const rejectForm = reactive({
  reason: ''
})

const currentTicket = ref({
  id: null,
  brand: '',
  store_code: '',
  complaint_type: '',
  handler: '',
  has_compensation: false,
  compensation_type: '',
  compensation_amount: 0,
  status: 'pending',
  is_closed: false,
  closing_remark: '',
  rejected_reason: '',
  created_at: '',
  updated_at: '',
  images: []
})

const ticketForm = reactive({
  brand: '',
  store_code: '',
  complaint_type: '',
  handler: '',
  has_compensation: false,
  compensation_type: '',
  compensation_amount: 0,
  is_closed: false,
  closing_remark: ''
})

const dialogTitle = computed(() => isEditMode.value ? '编辑工单' : '新增工单')
const uploadUrl = computed(() => {
  return isEditMode.value ? `http://127.0.0.1:8000/tickets/${currentTicketId.value}/images` : ''
})
const uploadHeaders = computed(() => ({}))

const filteredLogs = computed(() => {
  if (!logFilter.value) return operationLogs.value
  return operationLogs.value.filter(log => log.action === logFilter.value)
})

const validateCompensationType = (rule, value, callback) => {
  if (ticketForm.has_compensation && ticketForm.compensation_amount > 0 && !ticketForm.compensation_type) {
    callback(new Error('补偿金额大于0时必须选择补偿类型'))
  } else {
    callback()
  }
}

const formRules = {
  brand: [{ required: true, message: '请选择品牌', trigger: 'change' }],
  store_code: [{ required: true, message: '请输入门店编号', trigger: 'blur' }],
  complaint_type: [{ required: true, message: '请选择投诉类型', trigger: 'change' }],
  handler: [{ required: true, message: '请输入处理人', trigger: 'blur' }],
  compensation_type: [{ validator: validateCompensationType, trigger: 'change' }]
}

const getBrandTagType = (brand) => {
  const types = {
    '肯德基': 'danger',
    '麦当劳': 'warning',
    '华莱士': 'success'
  }
  return types[brand] || 'info'
}

const getStatusName = (status) => {
  const names = {
    'pending': '待受理',
    'processing': '处理中',
    'review': '待复核',
    'closed': '已结案'
  }
  return names[status] || status
}

const getStatusTagType = (status) => {
  const types = {
    'pending': 'info',
    'processing': 'warning',
    'review': 'primary',
    'closed': 'success'
  }
  return types[status] || 'info'
}

const getLogType = (action) => {
  const types = {
    'create': 'success',
    'update': 'primary',
    'delete': 'danger',
    'accept': 'primary',
    'process': 'warning',
    'review': 'primary',
    'close': 'success',
    'reject': 'danger',
    'upload_image': 'info',
    'delete_image': 'info'
  }
  return types[action] || 'info'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getImageUrl = (path) => {
  if (path.startsWith('http')) return path
  return path
}

const fetchTickets = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (filterForm.brand) params.brand = filterForm.brand
    if (filterForm.status) params.status = filterForm.status
    const res = await getTickets(params)
    tickets.value = res.data.items
    pagination.total = res.data.total
  } catch (err) {
    ElMessage.error('获取工单列表失败')
    console.error(err)
  } finally {
    loading.value = false
  }
}

const resetFilter = () => {
  filterForm.brand = ''
  filterForm.status = ''
  pagination.page = 1
  fetchTickets()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchTickets()
}

const handleSizeChange = (size) => {
  pagination.page_size = size
  pagination.page = 1
  fetchTickets()
}

const openCreateDialog = () => {
  isEditMode.value = false
  currentTicketId.value = null
  resetForm()
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  isEditMode.value = true
  currentTicketId.value = row.id
  Object.assign(ticketForm, {
    brand: row.brand,
    store_code: row.store_code,
    complaint_type: row.complaint_type,
    handler: row.handler,
    has_compensation: row.has_compensation,
    compensation_type: row.compensation_type || '',
    compensation_amount: row.compensation_amount || 0,
    is_closed: row.is_closed,
    closing_remark: row.closing_remark || ''
  })
  imageFileList.value = (row.images || []).map(img => ({
    name: img.original_name,
    url: img.file_path
  }))
  dialogVisible.value = true
}

const viewDetail = async (row) => {
  try {
    const res = await getTicket(row.id)
    currentTicket.value = res.data
    
    const logsRes = await getOperationLogs(row.id)
    operationLogs.value = logsRes.data
    logFilter.value = ''
    
    detailVisible.value = true
  } catch (err) {
    ElMessage.error('获取工单详情失败')
    console.error(err)
  }
}

const handleStatusTransition = async (action) => {
  try {
    transitioning.value = true
    await transitionStatus(currentTicket.value.id, { action })
    ElMessage.success('状态变更成功')
    
    await viewDetail({ id: currentTicket.value.id })
    fetchTickets()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '状态变更失败')
    console.error(err)
  } finally {
    transitioning.value = false
  }
}

const showRejectDialog = () => {
  rejectForm.reason = ''
  rejectDialogVisible.value = true
}

const handleReject = async () => {
  if (!rejectForm.reason.trim()) {
    ElMessage.warning('请填写驳回原因')
    return
  }
  
  try {
    transitioning.value = true
    await transitionStatus(currentTicket.value.id, {
      action: 'reject',
      rejected_reason: rejectForm.reason
    })
    ElMessage.success('工单已驳回')
    rejectDialogVisible.value = false
    
    await viewDetail({ id: currentTicket.value.id })
    fetchTickets()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '驳回失败')
    console.error(err)
  } finally {
    transitioning.value = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确定要删除该工单吗？删除后可通过数据库恢复。', '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteTicket(row.id)
      ElMessage.success('删除成功')
      fetchTickets()
    } catch (err) {
      ElMessage.error('删除失败')
      console.error(err)
    }
  }).catch(() => {})
}

const resetForm = () => {
  Object.assign(ticketForm, {
    brand: '',
    store_code: '',
    complaint_type: '',
    handler: '',
    has_compensation: false,
    compensation_type: '',
    compensation_amount: 0,
    is_closed: false,
    closing_remark: ''
  })
  imageFileList.value = []
  if (ticketFormRef.value) {
    ticketFormRef.value.resetFields()
  }
}

const submitForm = async () => {
  if (!ticketFormRef.value) return
  try {
    await ticketFormRef.value.validate()
    submitting.value = true
    
    if (isEditMode.value) {
      await updateTicket(currentTicketId.value, ticketForm)
      ElMessage.success('更新成功')
    } else {
      await createTicket(ticketForm)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    fetchTickets()
  } catch (err) {
    if (err !== false) {
      console.error(err)
      const errorMsg = err.response?.data?.detail || err.message || '操作失败'
      ElMessage.error(errorMsg)
    }
  } finally {
    submitting.value = false
  }
}

const handleUploadSuccess = (response, file) => {
  ElMessage.success('图片上传成功')
  fetchTickets()
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只允许上传图片文件')
    return false
  }
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }
  return true
}

const loadBaseData = async () => {
  try {
    const [brandsRes, typesRes, compRes, statusesRes, slaRes, actionsRes] = await Promise.all([
      getBrands(),
      getComplaintTypes(),
      getCompensationTypes(),
      getStatuses(),
      getSlaConfig(),
      getActions()
    ])
    brands.value = brandsRes.data.brands
    complaintTypes.value = typesRes.data.types
    compensationTypes.value = compRes.data.types
    statusOptions.value = statusesRes.data.statuses
    slaConfig.value = slaRes.data
    actionLabels.value = actionsRes.data.actions
  } catch (err) {
    console.error('加载基础数据失败', err)
  }
}

onMounted(() => {
  loadBaseData()
  fetchTickets()
})
</script>

<style scoped>
.ticket-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-card {
  border-radius: 8px;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.table-card {
  border-radius: 8px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.text-muted {
  color: #909399;
}

.sla-badge {
  display: inline-block;
  margin-left: 4px;
  padding: 2px 6px;
  font-size: 11px;
  border-radius: 3px;
  background-color: #e6a23c;
  color: white;
}

.sla-badge.sla-warning {
  background-color: #f56c6c;
}

.sla-badge.sla-breached {
  background-color: #f56c6c;
  font-weight: bold;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.detail-images {
  margin-top: 20px;
}

.detail-images h4 {
  margin-bottom: 12px;
  color: #303133;
}

.image-gallery {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.gallery-image {
  width: 120px;
  height: 120px;
  border-radius: 4px;
  cursor: pointer;
}

.status-actions {
  margin: 20px 0;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.status-actions h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.operation-timeline {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.operation-timeline h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.timeline-filter {
  margin-bottom: 16px;
}

.log-content {
  padding: 8px 0;
}

.log-detail {
  display: flex;
  gap: 16px;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.log-remark {
  margin-top: 4px;
  font-size: 13px;
  color: #606266;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-upload--picture-card) {
  width: 88px;
  height: 88px;
}

:deep(.el-upload-list--picture-card .el-upload-list__item) {
  width: 88px;
  height: 88px;
}

:deep(.el-timeline-item__content) {
  padding-bottom: 8px;
}
</style>