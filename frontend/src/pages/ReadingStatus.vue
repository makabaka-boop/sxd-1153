<template>
  <div class="reading-status-page">
    <a-card :bordered="false">
      <template #extra>
        <a-space>
          <a-select
        v-model:value="filterStatus"
        placeholder="阅读状态"
        style="width: 120px"
        allow-clear
        @change="loadData"
      >
        <a-select-option :value="true">已读</a-select-option>
        <a-select-option :value="false">未读</a-select-option>
      </a-select>
          <a-button @click="loadData">
            <ReloadOutlined /> 刷新
          </a-button>
        </a-space>
      </template>
      <a-row :gutter="[16, 16]" style="margin-bottom: 16px">
        <a-col :span="8">
          <a-card size="small">
            <a-statistic
              title="总条目"
              :value="stats.total"
              :value-style="{ color: '#1890ff' }"
            />
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small">
            <a-statistic
              title="已读"
              :value="stats.read"
              :value-style="{ color: '#52c41a' }"
            />
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small">
            <a-statistic
              title="未读"
              :value="stats.unread"
              :value-style="{ color: '#f5222d' }"
            />
          </a-card>
        </a-col>
      </a-row>
      <a-table
        :columns="columns"
        :data-source="readingList"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_read'">
            <a-tag v-if="record.is_read" color="green">已读</a-tag>
            <a-tag v-else color="red">未读</a-tag>
          </template>
          <template v-else-if="column.key === 'read_at'">
            <span v-if="record.read_at">{{ formatDate(record.read_at) }}</span>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="viewDetail(record)">查看</a-button>
              <a-button
                size="small"
                type="primary"
                v-if="!record.is_read"
                @click="handleMarkRead(record.knowledge_id)"
              >
                标记已读
              </a-button>
              <a-button
                size="small"
                v-else
                @click="handleMarkUnread(record.knowledge_id)"
              >
                标记未读
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

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
          </a-space>
        </div>
        <a-divider />
        <div class="detail-body" v-html="currentDetail.content"></div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import {
  getMyReadingStatus,
  type ReadingStatusItem
} from '@/api/reading'
import { getKnowledgeDetail, type KnowledgeItem } from '@/api/knowledge'
import { markAsRead, markAsUnread } from '@/api/reading'

const loading = ref(false)
const filterStatus = ref<boolean | undefined>()
const readingList = ref<ReadingStatusItem[]>([])
const currentDetail = ref<KnowledgeItem | null>(null)
const detailModalVisible = ref(false)

const stats = reactive({
  total: 0,
  read: 0,
  unread: 0
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
  { title: '知识标题', dataIndex: 'knowledge_title', key: 'knowledge_title', ellipsis: true },
  { title: '阅读状态', key: 'is_read', width: 100 },
  { title: '阅读时间', key: 'read_at', width: 180 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' }
]

const loadData = async () => {
  loading.value = true
  try {
    const res = await getMyReadingStatus({
      page: pagination.current,
      page_size: pagination.pageSize
    })
    if (res.code === 200) {
      const data = res.data
      readingList.value = data.items
      pagination.total = data.total
      
      stats.total = data.total
      stats.read = data.items.filter((item: ReadingStatusItem) => item.is_read).length
      stats.unread = data.items.filter((item: ReadingStatusItem) => !item.is_read).length
    }
  } finally {
    loading.value = false
  }
}

const handleTableChange = (p: any) => {
  pagination.current = p.current
  pagination.pageSize = p.pageSize
  loadData()
}

const viewDetail = async (item: ReadingStatusItem) => {
  try {
    const res = await getKnowledgeDetail(item.knowledge_id)
    if (res.code === 200) {
      currentDetail.value = res.data
      detailModalVisible.value = true
      if (!item.is_read) {
        await handleMarkRead(item.knowledge_id)
      }
    }
  } catch (e) {
    message.error('获取详情失败')
  }
}

const handleMarkRead = async (knowledgeId: number) => {
  const res = await markAsRead(knowledgeId)
  if (res.code === 200) {
    message.success('已标记为已读')
    loadData()
  }
}

const handleMarkUnread = async (knowledgeId: number) => {
  const res = await markAsUnread(knowledgeId)
  if (res.code === 200) {
    message.success('已标记为未读')
    loadData()
  }
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.reading-status-page {
  padding: 0;
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
</style>
