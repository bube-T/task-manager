import client from './client'
import type { Task, TaskCreate, TaskUpdate, Stats } from '../types'

export async function getTasks(params?: { status?: string; priority?: string }): Promise<Task[]> {
  const { data } = await client.get<Task[]>('/tasks/', { params })
  return data
}

export async function getTask(id: number): Promise<Task> {
  const { data } = await client.get<Task>(`/tasks/${id}`)
  return data
}

export async function createTask(body: TaskCreate): Promise<Task> {
  const { data } = await client.post<Task>('/tasks/', body)
  return data
}

export async function updateTask(id: number, body: TaskUpdate): Promise<Task> {
  const { data } = await client.patch<Task>(`/tasks/${id}`, body)
  return data
}

export async function deleteTask(id: number): Promise<void> {
  await client.delete(`/tasks/${id}`)
}

export async function getStats(): Promise<Stats> {
  const { data } = await client.get<Stats>('/tasks/stats/summary')
  return data
}
