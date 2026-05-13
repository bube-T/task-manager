export interface User {
  id: number
  email: string
  created_at: string
}

export interface Task {
  id: number
  title: string
  description: string | null
  priority: 'low' | 'medium' | 'high'
  status: 'pending' | 'completed'
  due_date: string | null
  created_at: string
  completed_at: string | null
  owner_id: number
  recurrence: string
  note_count: number
}

export interface TaskCreate {
  title: string
  description?: string
  priority?: 'low' | 'medium' | 'high'
  status?: 'pending' | 'completed'
  due_date?: string | null
  recurrence?: string
}

export interface TaskUpdate {
  title?: string
  description?: string | null
  priority?: 'low' | 'medium' | 'high'
  status?: 'pending' | 'completed'
  due_date?: string | null
  completed_at?: string | null
  recurrence?: string
}

export interface Note {
  id: number
  task_id: number
  owner_id: number
  content: string
  created_at: string
}

export interface Stats {
  total: number
  completed: number
  pending: number
  overdue: number
}

export interface Token {
  access_token: string
  token_type: string
}
