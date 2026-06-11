import request from './request'

export interface Group {
  id: number
  name: string
  description: string
  created_at: string
}

export interface GroupCreate {
  name: string
  description?: string
}

export interface GroupUpdate {
  name?: string
  description?: string
}

export function getGroups() {
  return request<Group[]>({
    url: '/groups',
    method: 'GET'
  })
}

export function getGroup(id: number) {
  return request<Group>({
    url: `/groups/${id}`,
    method: 'GET'
  })
}

export function createGroup(data: GroupCreate) {
  return request<Group>({
    url: '/groups',
    method: 'POST',
    data
  })
}

export function updateGroup(id: number, data: GroupUpdate) {
  return request<Group>({
    url: `/groups/${id}`,
    method: 'PUT',
    data
  })
}

export function deleteGroup(id: number) {
  return request({
    url: `/groups/${id}`,
    method: 'DELETE'
  })
}
