import { useState, useEffect } from 'react'

function App() {
  const [sensors, setSensors] = useState<any[]>([])
  const [tasks, setTasks] = useState<any[]>([])

  useEffect(() => {
    fetch('http://localhost:8001/api/v1/sensors/history')
      .then(res => res.json())
      .then(data => setSensors(data))

    fetch('http://localhost:8001/api/v1/tasks/history')
      .then(res => res.json())
      .then(data => setTasks(data))
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-800">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold text-emerald-700">🌿 Smart Eco-Farm</h1>
          <p className="text-slate-500">React Dashboard Edge Node</p>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-slate-400 text-sm font-bold tracking-wider mb-2">TEMP</h3>
          <p className="text-3xl font-bold text-slate-800">{sensors[0]?.temperature || '--'}°C</p>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-slate-400 text-sm font-bold tracking-wider mb-2">HUMIDITY</h3>
          <p className="text-3xl font-bold text-slate-800">{sensors[0]?.humidity || '--'}%</p>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-slate-400 text-sm font-bold tracking-wider mb-2">SOIL</h3>
          <p className="text-3xl font-bold text-slate-800">{sensors[0]?.soil_moisture || '--'}%</p>
        </div>
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 className="text-slate-400 text-sm font-bold tracking-wider mb-2">LUX</h3>
          <p className="text-3xl font-bold text-slate-800">{sensors[0]?.lux || '--'}</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 mb-8">
        <h2 className="text-xl font-bold mb-4">Latest AI Detections</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 text-slate-400">
                <th className="py-3 px-4 font-semibold text-sm">Status</th>
                <th className="py-3 px-4 font-semibold text-sm">Diagnosis</th>
                <th className="py-3 px-4 font-semibold text-sm">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map(t => (
                <tr key={t.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-4">
                    <span className="bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-xs font-bold">{t.status}</span>
                  </td>
                  <td className="py-3 px-4 font-medium">{t.diagnosis_result}</td>
                  <td className="py-3 px-4">{(t.confidence * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default App
