import { Play, RefreshCw } from 'lucide-react';
import BackgroundPattern from './BackgroundPattern';
import Header from './Header';
import { useEffect, useState } from 'react';

interface DashboardProps {
  onNavigateToFAQ: () => void;
  onNavigateToSimulation: () => void;
  onLogout: () => void;
}

export default function Dashboard({ onNavigateToFAQ, onNavigateToSimulation, onLogout }: DashboardProps) {
  const [conversaciones, setConversaciones] = useState<any[]>([]);
  const [running, setRunning] = useState(false);

  const loadConversaciones = async () => {
    const urls = ['/api/conversaciones', 'http://localhost:5001/api/conversaciones'];
    for (const url of urls) {
      try {
        const res = await fetch(url, { method: 'GET' });
        // si no es JSON o devuelve 404, intentamos el siguiente
        if (!res.ok) {
          console.warn('Non-ok response from', url, res.status);
          continue;
        }
        const text = await res.text();
        try {
          const data = JSON.parse(text);
          setConversaciones(data.conversaciones || []);
          return;
        } catch (err) {
          console.warn('Response from', url, 'was not JSON; trying next', err);
          continue;
        }
      } catch (e) {
        console.warn('Error fetching from', url, e);
        continue;
      }
    }
    console.error('Error cargando conversaciones: todas las vías fallaron');
  };

  useEffect(() => {
    loadConversaciones();
  }, []);

  const handleStartRegistro = async () => {
    setRunning(true);
    const urls = ['/api/run_llamada', 'http://localhost:5001/api/run_llamada'];
    let jobId: string | null = null;
    for (const url of urls) {
      try {
        const res = await fetch(url, { method: 'POST' });
        if (res.ok) {
          const data = await res.json();
          jobId = data.job_id || data.jobId || null;
          break;
        }
        console.warn('run_llamada non-ok', url, res.status);
      } catch (e) {
        console.warn('run_llamada error', url, e);
      }
    }
    if (!jobId) {
      alert('Error al iniciar la simulación (no se pudo contactar al backend)');
      setRunning(false);
      return;
    }
    // Abrir stream SSE para recibir eventos en tiempo real
    const streamUrls = [`/api/run_llamada/stream/${jobId}`, `http://localhost:5001/api/run_llamada/stream/${jobId}`];
    let es: EventSource | null = null;
    let connected = false;

    for (const s of streamUrls) {
      try {
        es = new EventSource(s);
        connected = true;
        break;
      } catch (e) {
        console.warn('EventSource fallo para', s, e);
        es = null;
      }
    }

    if (!connected || !es) {
      // fallback a polling si no hay SSE
      const statusUrls = [`/api/run_llamada/status/${jobId}`, `http://localhost:5001/api/run_llamada/status/${jobId}`];
      let finished = false;
      try {
        while (!finished) {
          for (const sUrl of statusUrls) {
            try {
              const r = await fetch(sUrl);
              if (!r.ok) continue;
              const js = await r.json();
              const info = js.job;
              if (!info) continue;
              if (info.status && info.status !== 'running') {
                finished = true;
                await loadConversaciones();
                break;
              }
              await new Promise((res) => setTimeout(res, 1000));
            } catch (e) {
              continue;
            }
          }
        }
      } catch (e) {
        console.error('Error polling job status', e);
        alert('Error comprobando el estado del job');
      } finally {
        setRunning(false);
      }
      return;
    }

    // Si tenemos EventSource, manejamos eventos en tiempo real
    es.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === 'message') {
          // Mapear al formato de la tabla
          const newRow = {
            id: Date.now() + Math.random(),
            timestamp: data.timestamp || new Date().toISOString(),
            personaje: data.personaje,
            mensaje: data.mensaje,
            turno: data.turno,
            duracion_segundos: data.duracion_segundos || 0,
          };
          // Agregar al inicio para que la tabla muestre lo más reciente arriba
          setConversaciones((prev) => [newRow, ...prev]);
        } else if (data.type === 'job_done' || (data.type === 'job_status' && data.status)) {
          // cerrar stream y recargar
          try { es.close(); } catch (_) {}
          setRunning(false);
          loadConversaciones();
        }
      } catch (e) {
        console.warn('Error parseando evento SSE', e);
      }
    };

    es.onerror = (err) => {
      console.warn('SSE error', err);
      try { es && es.close(); } catch (_) {}
      setRunning(false);
      loadConversaciones();
    };
  };
  const handleNavigate = (page: 'dashboard' | 'faq' | 'simulation') => {
    if (page === 'faq') onNavigateToFAQ();
    if (page === 'simulation') onNavigateToSimulation();
  };

  return (
    <div className="min-h-screen relative">
      <BackgroundPattern />
      
      <div className="relative z-10">
        <Header 
          currentPage="dashboard" 
          onNavigate={handleNavigate}
          onLogout={onLogout}
        />

        {/* Main Content */}
        <main className="px-8 py-12">
          <div className="max-w-6xl mx-auto">
            {/* Title */}
            <h1 className="text-white mb-12 text-[4.25rem] leading-[1.05] text-center">
              Registro de llamadas
            </h1>

            {/* Controls */}
            <div className="flex items-center justify-between mb-4">
              <div />
              <div>
                <button
                  onClick={handleStartRegistro}
                  disabled={running}
                  className="px-4 py-2 rounded-full bg-[#3bb3a9] text-white flex items-center gap-2 hover:opacity-90 disabled:opacity-50"
                  title="Iniciar llamada"
                >
                  <Play size={16} />
                  <span>Iniciar llamada</span>
                </button>
                {/* Visual de llamada en curso */}
                <div className="mt-6">
                  {running ? (
                    <div className="w-full flex items-center gap-4 bg-white/6 border border-white/20 rounded-xl px-6 py-4">
                      <div className="flex-shrink-0">
                        <div className="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center animate-pulse">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M3 12h3m4 0h8" stroke="#064e47" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="text-white text-2xl font-semibold">Conversación en curso</div>
                        <div className="text-white/70 mt-1">Se están intercambiando mensajes entre las IAs. Ver el registro en tiempo real abajo.</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-white/80 rounded-md animate-[pulse_1.2s_infinite]" />
                        <div className="w-6 h-6 bg-white/60 rounded-md animate-[pulse_1.2s_infinite_0.2s]" />
                        <div className="w-6 h-6 bg-white/40 rounded-md animate-[pulse_1.2s_infinite_0.4s]" />
                      </div>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>

            {/* Table */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl overflow-hidden border border-white/20">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/20">
                    <th className="px-8 py-4 text-left text-white">Fecha</th>
                    <th className="px-8 py-4 text-left text-white">Personaje</th>
                    <th className="px-8 py-4 text-left text-white">Mensaje</th>
                    <th className="px-8 py-4 text-left text-white">Turno</th>
                    <th className="px-8 py-4 text-left text-white">Duración (s)</th>
                  </tr>
                </thead>
                <tbody>
                  {conversaciones.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-8 py-6 text-white/70">No hay conversaciones registradas.</td>
                    </tr>
                  )}
                  {conversaciones.map((c, idx) => (
                    <tr key={c.id || idx} className="border-b border-white/20 hover:bg-white/5 transition-colors">
                      <td className="px-8 py-6 text-white/70">{new Date(c.timestamp).toLocaleString()}</td>
                      <td className="px-8 py-6 text-white/70">{c.personaje}</td>
                      <td className="px-8 py-6 text-white/70 max-w-[40ch] truncate">{c.mensaje}</td>
                      <td className="px-8 py-6 text-white/70">{c.turno}</td>
                      <td className="px-8 py-6 text-white/70">{Number(c.duracion_segundos).toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
