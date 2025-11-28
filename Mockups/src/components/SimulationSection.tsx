import { useState } from 'react';
import { Plus, FileText, RotateCcw, Trash2 } from 'lucide-react';
import BackgroundPattern from './BackgroundPattern';
import Header from './Header';

interface SimulationSectionProps {
  onBack: () => void;
}

interface Agent {
  id: number;
  name: string;
}

interface Client {
  id: number;
  name: string;
}

export default function SimulationSection({ onBack }: SimulationSectionProps) {
  const [agents, setAgents] = useState<Agent[]>([
    { id: 1, name: 'AGENTE 1' },
    { id: 2, name: 'AGENTE 2' },
  ]);

  const [clients, setClients] = useState<Client[]>([
    { id: 1, name: 'CLIENTE 1' },
    { id: 2, name: 'CLIENTE 2' },
  ]);

  const handleNavigate = (page: 'dashboard' | 'faq' | 'simulation') => {
    if (page === 'dashboard') onBack();
    // Otras navegaciones se manejarían aquí
  };

  const handleSimular = () => {
    // Inicia flujo: pedir pregunta de ejemplo y pedir respuesta al backend
    (async () => {
      try {
        // Generar pregunta
        const qRes = await fetch('/api/generate_question', { method: 'POST' });
        const qData = await qRes.json();
        const question = qData.question;

        // Añadir al chat local
        setChat((c) => [...c, { who: 'Alumno', text: question }]);

        // Llamar al backend para obtener la respuesta de la profesora
        const r = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: question, role: 'student' }),
        });
        const reply = await r.json();
        setChat((c) => [...c, { who: 'Profesora', text: reply.reply }]);
      } catch (err) {
        alert('Error iniciando simulación');
      }
    })();
  };

  // Chat simple mostrado en la UI
  const [chat, setChat] = useState<{ who: string; text: string }[]>([]);

  return (
    <div className="min-h-screen relative">
      <BackgroundPattern />
      
      <div className="relative z-10">
        <Header 
          currentPage="simulation" 
          onNavigate={handleNavigate}
          onLogout={() => {}}
        />

        {/* Main Content */}
        <main className="px-8 py-12">
          <div className="max-w-5xl mx-auto">
            {/* Title */}
            <h1 className="text-white mb-12 text-[4.25rem] leading-[1.05] text-center">
              Simulación
            </h1>

            {/* Agent Section */}
            <div className="mb-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl overflow-hidden border border-white/20">
                {/* Header */}
                <div className="flex items-center justify-between px-8 py-4 border-b border-white/20">
                  <div className="text-white">AGENTE</div>
                  <div className="text-white">ARCHIVO</div>
                  <button
                    className="w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 transition-colors flex items-center justify-center"
                    title="Agregar"
                    aria-label="Agregar"
                  >
                    <Plus size={24} className="text-white" />
                  </button>
                </div>

                {/* Agent List */}
                {agents.map((agent, index) => (
                  <div 
                    key={agent.id}
                    className={`flex items-center justify-between px-8 py-4 ${
                      index < agents.length - 1 ? 'border-b border-white/20' : ''
                    }`}
                  >
                    <div className="text-white flex-1">{agent.name}</div>
                    <div className="flex items-center gap-6">
                      <FileText size={28} className="text-white" />
                      <button className="hover:opacity-80 transition-opacity" title="Reintentar" aria-label="Reintentar">
                        <RotateCcw size={28} className="text-white" />
                      </button>
                      <button className="hover:opacity-80 transition-opacity" title="Eliminar" aria-label="Eliminar">
                        <Trash2 size={28} className="text-white" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Client Section */}
            <div className="mb-12">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl overflow-hidden border border-white/20">
                {/* Header */}
                <div className="flex items-center justify-between px-8 py-4 border-b border-white/20">
                  <div className="text-white">CLIENTE</div>
                  <div className="text-white">ARCHIVO</div>
                  <button
                    className="w-10 h-10 rounded-full bg-white/20 hover:bg-white/30 transition-colors flex items-center justify-center"
                    title="Agregar"
                    aria-label="Agregar"
                  >
                    <Plus size={24} className="text-white" />
                  </button>
                </div>

                {/* Client List */}
                {clients.map((client, index) => (
                  <div 
                    key={client.id}
                    className={`flex items-center justify-between px-8 py-4 ${
                      index < clients.length - 1 ? 'border-b border-white/20' : ''
                    }`}
                  >
                    <div className="text-white flex-1">{client.name}</div>
                    <div className="flex items-center gap-6">
                      <FileText size={28} className="text-white" />
                      <button className="hover:opacity-80 transition-opacity" title="Reintentar" aria-label="Reintentar">
                        <RotateCcw size={28} className="text-white" />
                      </button>
                      <button className="hover:opacity-80 transition-opacity" title="Eliminar" aria-label="Eliminar">
                        <Trash2 size={28} className="text-white" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Simular Button */}
            <div className="flex justify-center">
              <button
                onClick={handleSimular}
                className="px-16 py-4 rounded-full text-white transition-opacity hover:opacity-90 bg-[#4a6b82] text-xl"
              >
                SIMULAR
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
