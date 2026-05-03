import client from './client'
import type { Token, User } from '../types'

export async function register(email: string, password: string): Promise<User> {
  const { data } = await client.post<User>('/auth/register', { email, password })
  return data
}

export async function login(email: string, password: string): Promise<Token> {
  const params = new URLSearchParams({ username: email, password })
  const { data } = await client.post<Token>('/auth/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export async function getMe(): Promise<User> {
  const { data } = await client.get<User>('/auth/me')
  return data
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await client.patch('/auth/password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}
