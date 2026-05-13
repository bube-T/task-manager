import client from './client'
import type { Note } from '../types'

export async function getNotes(taskId: number): Promise<Note[]> {
  const { data } = await client.get<Note[]>(`/tasks/${taskId}/notes/`)
  return data
}

export async function createNote(taskId: number, content: string): Promise<Note> {
  const { data } = await client.post<Note>(`/tasks/${taskId}/notes/`, { content })
  return data
}

export async function deleteNote(taskId: number, noteId: number): Promise<void> {
  await client.delete(`/tasks/${taskId}/notes/${noteId}`)
}
