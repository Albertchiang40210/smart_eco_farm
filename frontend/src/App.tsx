import { useCallback, useEffect, useState } from 'react'
import {
  fetchSensors, fetchTasks, getToken, logout, UnauthorizedError,
  type DetectionTask, type SensorReading,
} from './api'
import Login from './Login'

const REFRESH_MS = 10_000

function Stat({ label, value, unit }: { label: string; value?: number; unit: string }) {
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
      <h3 className="text-slate-400 text-sm font-bold tracking-wider mb-2">{label}</h3>
      <p className="text-3xl font-bold text-slate-800">{value ?? '--'}{value !== undefined && unit}</p>
    </div>
  )
}

function Dashboard({ onLogout }: { onLogout: () => void }) {
  const [sensors, setSensors] = useState<SensorReading[]>([])
  const [tasks, setTasks] = useState<DetectionTask[]>([])
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([fetchSensors(), fetchTasks()])
      setSensors(s)
      setTasks(t)
      setError('')
    } catch (err) {
      if (err instanceof UnauthorizedError) onLogout()
      else setError('無法連線到後端，稍後自動重試')
    }
  }, [onLogout])

  useEffect(() => {
    load()
    const timer = setInterval(load, REFRESH_MS)
    return () => clearInterval(timer)
  }, [load])

  const latest = sensors[0]

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-800">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-emerald-700">🌿 Smart Eco-Farm</h1>
          <p className="text-slate-500">
            {latest ? `最後更新 ${new Date(latest.created_at + 'Z').toLocaleTimeString()}` : '尚無感測資料'}
          </p>
        </div>
        <button onClick={() => { logout(); onLogout() }} className="text-sm text-slate-500 hover:text-slate-800">登出</button>
      </header>

      {error && <div className="mb-6 p-3 rounded-lg bg-amber-50 text-amber-800 text-sm">{error}</div>}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Stat label="TEMP" value={latest?.temperature} unit="°C" />
        <Stat label="HUMIDITY" value={latest?.humidity} unit="%" />
        <Stat label="SOIL" value={latest?.soil_moisture} unit="%" />
        <Stat label="LUX" value={latest?.lux} unit=" lx" />
      </div>

      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h2 className="text-xl font-bold mb-4">Latest AI Detections</h2>
        {tasks.length === 0 ? (
          <p className="text-slate-400 text-sm">尚無偵測紀錄</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 text-sm">
                  <th className="py-3 px-4 font-semibold">Time</th>
                  <th className="py-3 px-4 font-semibold">Diagnosis</th>
                  <th className="py-3 px-4 font-semibold">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map(t => (
                  <tr key={t.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 text-sm text-slate-500">{new Date(t.created_at + 'Z').toLocaleString()}</td>
                    <td className="py-3 px-4 font-medium">{t.diagnosis_result}</td>
                    <td className="py-3 px-4">{(t.confidence * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [authed, setAuthed] = useState(() => !!getToken())
  const handleLogout = useCallback(() => setAuthed(false), [])
  return authed ? <Dashboard onLogout={handleLogout} /> : <Login onSuccess={() => setAuthed(true)} />
}
