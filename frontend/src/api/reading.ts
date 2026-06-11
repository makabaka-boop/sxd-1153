import request, { type ApiResponse } from './request'
import type { ReviewExpiryStatus } from './knowledge'

export interface ReadingStatusItem {
  id: number
  knowledge_id: number
  knowledge_title?: string
  user_id: number
  is_read: boolean
  read_at: string
  review_status?: string
  suggested_review_cycle?: string
  next_review_date?: string
  review_expiry_status?: ReviewExpiryStatus
}

export const markAsRead = (knowledge_id: number) => {
  return request.post<any, ApiResponse>(`/reading/${knowledge_id}`)
}

export const markAsUnread = (knowledge_id: number) => {
  return request.delete<any, ApiResponse>(`/reading/${knowledge_id}`)
}

export const getMyReadingStatus = (params: {
  page?: number
  page_size?: number
  review_expiry_status?: string
}) => {
  return request.get<any, ApiResponse<{
    items: ReadingStatusItem[]
    total: number
    page: number
    page_size: number
  }>>('/reading/my-status', { params })
}
