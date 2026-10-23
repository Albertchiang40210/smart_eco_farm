import { useState, type FormEvent } from 'react'
import { login } from './api'

export default function Login({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    try {
      await login(username, password)
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : '登入失敗')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <form onSubmit={submit} className="bg-white p-8 rounded-2xl shadow-sm border border-slate-100 w-full max-w-sm">
        <h1 className="text-2xl font-extrabold text-emerald-700 mb-6">🌿 Smart Eco-Farm</h1>
        <input
          className="w-full border border-slate-200 rounded-lg px-3 py-2 mb-3"
          placeholder="帳號"
          autoComplete="username"
          value={username}
          onChange={e => setUsername(e.target.value)}
        />
        <input
          className="w-full border border-slate-200 rounded-lg px-3 py-2 mb-3"
          type="password"
          placeholder="密碼"
          autoComplete="current-password"
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
        {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
        <button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-lg">登入</button>
      </form>
    </div>
  )
}
