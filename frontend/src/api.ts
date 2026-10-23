const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8001'
const TOKEN_KEY = 'farm_token'

export interface SensorReading {
  temperature: number
  humidity: number
  soil_moisture: number
  lux: number
  created_at: string
}

export interface DetectionTask {
  id: number
  status: string
  diagnosis_result: string
  confidence: number
  created_at: string
}

export class UnauthorizedError extends Error {}

export const getToken = () => sessionStorage.getItem(TOKEN_KEY)
export const logout = () => sessionStorage.removeItem(TOKEN_KEY)

export async function login(username: string, password: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/v1/login`, {
    method: 'POST',
    body: new URLSearchParams({ username, password }),
  })
  if (!res.ok) throw new Error('帳號或密碼錯誤')
  const { access_token } = await res.json()
  sessionStorage.setItem(TOKEN_KEY, access_token)
}

async function authedGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  })
  if (res.status === 401) {
    logout()
    throw new UnauthorizedError()
  }
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const fetchSensors = () => authedGet<SensorReading[]>('/api/v1/sensors/history')
export const fetchTasks = () => authedGet<DetectionTask[]>('/api/v1/tasks/history')
