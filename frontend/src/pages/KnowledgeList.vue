<template>
  <div class="knowledge-page">
    <a-row :gutter="16">
      <a-col :xs="24" :lg="8">
        <a-card :bordered="false" class="tree-card">
          <CategoryTree
            ref="treeRef"
            @select="handleCategorySelect"
            @node-change="loadKnowledge"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="16">
        <a-card :bordered="false" class="list-card">
          <template #extra>
            <a-space>
              <a-input-search
                v-model:value="searchKeyword"
                placeholder="搜索标题或内容"
                style="width: 200px"
                @search="loadKnowledge"
              />
              <a-select
                v-model:value="statusFilter"
                placeholder="状态筛选"
                style="width: 120px"
                allow-clear
                @change="loadKnowledge"
              >
                <a-select-option value="approved">已通过</a-select-option>
                <a-select-option value="pending">待复核</a-select-option>
                <a-select-option value="rejected">已驳回</a-select-option>
              </a-select>
              <a-button
                type="primary"
                @click="openCreateModal"
                v-if="!userStore.hasRole('admin')"
              >
                <PlusOutlined /> 提交知识
              </a-button>
              <a-button @click="loadKnowledge">
                <ReloadOutlined /> 刷新
              </a-button>
              <a-button
                v-if="userStore.hasRole('supervisor')"
                type="primary"
                ghost
                @click="handleExport"
              >
                <DownloadOutlined /> 导出Excel
              </a-button>
            </a-space>
          </template>

          <div v-if="selectedCategory" class="selected-info">
            <a-alert
              :message="`当前分类: ${selectedCategory.name}`"
              type="info"
              show-icon
            >
              <template #description>
                <template v-if="currentSummary">
                  条目总数: {{ currentSummary.total_count }} |
                  未读: {{ currentSummary.unread_count }} |
                  待复核: {{ currentSummary.pending_count }}
                </template>
              </template>
            </a-alert>
          </div>

          <a-table
            :columns="columns"
            :data-source="knowledgeList"
            :loading="loading"
            :pagination="pagination"
            :row-selection="rowSelection"
            :scroll="{ x: 1000 }"
            row-key="id"
            @change="handleTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'title'">
                <a @click="viewDetail(record)">{{ record.title }}</a>
              </template>
              <template v-else-if="column.key === 'review_status'">
                <a-tag :color="getStatusColor(record.review_status)">
                  {{ getStatusLabel(record.review_status) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'is_read'">
                <a-tag v-if="record.is_read" color="green">已读</a-tag>
                <a-tag v-else color="red">未读</a-tag>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button size="small" @click="viewDetail(record)">查看</a-button>
                  <a-button
                    size="small"
                    v-if="!record.is_read"
                    type="primary"
                    @click="handleMarkRead(record.id)"
                  >
                    标记已读
                  </a-button>
                  <a-button
                    size="small"
                    v-else
                    @click="handleMarkUnread(record.id)"
                  >
                    标记未读
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="detailModalVisible"
      title="知识详情"
      width="800px"
      :footer="null"
    >
      <div v-if="currentDetail" class="detail-content">
        <h2>{{ currentDetail.title }}</h2>
        <div class="detail-meta">
          <a-space>
            <span>分类: {{ currentDetail.category_name }}</span>
            <span>提交人: {{ currentDetail.submitter_name }}</span>
            <span>{{ formatDate(currentDetail.created_at) }}</span>
            <a-tag :color="getStatusColor(currentDetail.review_status)">
              {{ getStatusLabel(currentDetail.review_status) }}
            </a-tag>
          </a-space>
        </div>
        <a-divider />
        <div class="detail-body" v-html="currentDetail.content"></div>
      </div>
    </a-modal>

    <a-modal
      v-model:open="createModalVisible"
      title="提交知识条目"
      width="700px"
      @ok="handleSubmit"
      :confirm-loading="submitting"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        layout="vertical"
      >
        <a-form-item label="标题" name="title">
          <a-input v-model:value="formData.title" placeholder="请输入知识标题" />
        </a-form-item>
        <a-form-item label="分类" name="category_id">
          <a-tree-select
            v-model:value="formData.category_id"
            :tree-data="treeSelectData"
            placeholder="请选择分类"
            style="width: 100%"
            :field-names="{ children: 'children', label: 'name', value: 'id' }"
            tree-default-expand-all
          />
        </a-form-item>
        <a-form-item label="内容" name="content">
          <a-textarea
            v-model:value="formData.content"
            :rows="10"
            placeholder="请输入知识内容，支持HTML格式"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import {
  PlusOutlined,
  ReloadOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue'
import { Modal, message } from 'ant-design-vue'
import CategoryTree from '@/components/CategoryTree.vue'
import { useUserStore } from '@/stores/user'
import { useCategoryStore } from '@/stores/category'
import {
  getKnowledgeList,
  createKnowledge,
  type KnowledgeItem,
  type KnowledgeCreate,
  type KnowledgeListResponse
} from '@/api/knowledge'
import { markAsRead, markAsUnread } from '@/api/reading'
import { getNodeSummary, type NodeSummary } from '@/api/summary'
import type { Rule } from 'ant-design-vue/es/form'

const route = useRoute()
const userStore = useUserStore()
const categoryStore = useCategoryStore()

const treeRef = ref()
const formRef = ref()
const loading = ref(false)
const submitting = ref(false)
const searchKeyword = ref('')
const statusFilter = ref<string | undefined>()
const selectedRowKeys = ref<number[]>([])
const knowledgeList = ref<KnowledgeItem[]>([])
const currentDetail = ref<KnowledgeItem | null>(null)
const detailModalVisible = ref(false)
const createModalVisible = ref(false)
const currentSummary = ref<NodeSummary | null>(null)

const selectedCategory = computed(() => categoryStore.selectedCategory)

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const formData = reactive<KnowledgeCreate>({
  title: '',
  content: '',
  category_id: 0
})

const formRules: Record<string, Rule[]> = {
  title: [{ required: true, message: '请输入标题' }],
  category_id: [{ required: true, message: '请选择分类' }],
  content: [{ required: true, message: '请输入内容' }]
}

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '分类', dataIndex: 'category_name', key: 'category_name', width: 120 },
  { title: '提交人', dataIndex: 'submitter_name', key: 'submitter_name', width: 100 },
  { title: '状态', key: 'review_status', width: 90 },
  { title: '阅读状态', key: 'is_read', width: 90 },
  { title: '提交时间', dataIndex: 'created_at', key: 'created_at', width: 170 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' }
]

const rowSelection = {
  selectedRowKeys: selectedRowKeys,
  onChange: (keys: number[]) => {
    selectedRowKeys.value = keys
  }
}

const treeSelectData = computed(() => {
  const filterActive = (nodes: any[]): any[] => {
    return nodes
      .filter((n: any) => n.is_active)
      .map((n: any) => ({
        ...n,
        children: n.children ? filterActive(n.children) : undefined
      }))
  }
  return filterActive(categoryStore.treeData)
})

const loadKnowledge = async () => {
  loading.value = true
  try {
    const params = {
      category_id: categoryStore.selectedCategoryId || undefined,
      page: pagination.current,
      page_size: pagination.pageSize,
      review_status: statusFilter.value,
      keyword: searchKeyword.value || undefined
    }
    const res = await getKnowledgeList(params)
    if (res.code === 200) {
      const data = res.data as KnowledgeListResponse
      knowledgeList.value = data.items
      pagination.total = data.total
    }
  } finally {
    loading.value = false
  }
}

const loadSummary = async () => {
  if (!categoryStore.selectedCategoryId) {
    currentSummary.value = null
    return
  }
  try {
    const res = await getNodeSummary(categoryStore.selectedCategoryId)
    if (res.code === 200) {
      currentSummary.value = res.data
    }
  } catch (e) {
    console.error('Load summary failed:', e)
  }
}

const handleCategorySelect = () => {
  pagination.current = 1
  loadKnowledge()
  loadSummary()
}

const handleTableChange = (p: any) => {
  pagination.current = p.current
  pagination.pageSize = p.pageSize
  loadKnowledge()
}

const viewDetail = async (item: KnowledgeItem) => {
  currentDetail.value = item
  detailModalVisible.value = true
  if (!item.is_read) {
    await handleMarkRead(item.id)
  }
}

const handleMarkRead = async (id: number) => {
  const res = await markAsRead(id)
  if (res.code === 200) {
    message.success('已标记为已读')
    loadKnowledge()
    loadSummary()
    treeRef.value?.reloadSummaries()
  }
}

const handleMarkUnread = async (id: number) => {
  const res = await markAsUnread(id)
  if (res.code === 200) {
    message.success('已标记为未读')
    loadKnowledge()
    loadSummary()
    treeRef.value?.reloadSummaries()
  }
}

const openCreateModal = () => {
  formData.category_id = categoryStore.selectedCategoryId || 0
  formData.title = ''
  formData.content = ''
  createModalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    const res = await createKnowledge(formData)
    if (res.code === 200) {
      message.success('提交成功，等待主管复核')
      createModalVisible.value = false
      loadKnowledge()
      loadSummary()
      treeRef.value?.reloadSummaries()
    }
  } finally {
    submitting.value = false
  }
}

const handleExport = async () => {
  Modal.confirm({
    title: '确认导出',
    content: '确定要导出当前筛选条件下的知识清单吗？',
    async onOk() {
      try {
        const res = await fetch('/api/export/knowledge', {
          headers: {
            'Authorization': `Bearer ${userStore.token}`
          }
        })
        if (res.ok) {
          const blob = await res.blob()
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `知识清单_${new Date().toISOString().slice(0, 10)}.xlsx`
          a.click()
          window.URL.revokeObjectURL(url)
          message.success('导出成功')
        }
      } catch (e) {
        message.error('导出失败')
      }
    }
  })
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'orange',
    approved: 'green',
    rejected: 'red'
  }
  return colors[status] || 'default'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: '待复核',
    approved: '已通过',
    rejected: '已驳回'
  }
  return labels[status] || status
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(async () => {
  await categoryStore.fetchTree()
  await loadKnowledge()
  if (route.query.id) {
    const item = knowledgeList.value.find(k => k.id === Number(route.query.id))
    if (item) viewDetail(item)
  }
})
</script>

<style scoped>
.knowledge-page {
  padding: 0;
}

.tree-card,
.list-card {
  height: calc(100vh - 144px);
  display: flex;
  flex-direction: column;
}

.tree-card :deep(.ant-card-body),
.list-card :deep(.ant-card-body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.selected-info {
  margin-bottom: 16px;
}

.detail-content h2 {
  margin: 0 0 12px;
}

.detail-meta {
  color: #999;
  font-size: 14px;
}

.detail-body {
  margin-top: 16px;
  line-height: 1.8;
  font-size: 15px;
}

.detail-body :deep(p) {
  margin: 0 0 12px;
}
</style>
