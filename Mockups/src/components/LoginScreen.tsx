import { useState } from 'react';
import logoImage from 'figma:asset/f0133992c7469b5e53a97efe8573c8c5576abf33.png';
import BackgroundPattern from './BackgroundPattern';

interface LoginScreenProps {
  onLogin: () => void;
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [usuario, setUsuario] = useState('');
  const [contrasena, setContrasena] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Llamada al backend para login
    fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: usuario, password: contrasena }),
    })
      .then(async (res) => {
        const data = await res.json();
        if (res.ok && data.ok) {
          onLogin();
        } else {
          alert(data.error || 'Credenciales incorrectas');
        }
      })
      .catch(() => alert('Error conectando al servidor'));
  };

  return (
    <div className="min-h-screen relative flex items-center justify-center">
      <BackgroundPattern />
      
      <div className="relative z-10 w-full max-w-5xl mx-4">
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl overflow-hidden border border-white/20">
          <div className="grid grid-cols-2">
            {/* Left Panel - Logo */}
            <div className="bg-white/5 flex flex-col items-center justify-center p-16 border-r border-white/20">
              <img src={logoImage} alt="Aivox" className="h-32 w-32 object-contain" />
            </div>

            {/* Right Panel - Form */}
            <div className="p-16 flex flex-col justify-center">
              <h1 className="text-white mb-12 text-[3rem] leading-[1.05] text-center">Iniciar sesión</h1>
              
              <form onSubmit={handleSubmit} className="space-y-8">
                <div>
                  <label htmlFor="usuario" className="block text-white/70 mb-2">
                    Usuario
                  </label>
                  <input
                    id="usuario"
                    type="text"
                    value={usuario}
                    onChange={(e) => setUsuario(e.target.value)}
                    className="w-full px-4 py-3 border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent bg-white/5 text-white placeholder-white/30"
                    placeholder=""
                  />
                </div>

                <div>
                  <label htmlFor="contrasena" className="block text-white/70 mb-2">
                    Contraseña
                  </label>
                  <input
                    id="contrasena"
                    type="password"
                    value={contrasena}
                    onChange={(e) => setContrasena(e.target.value)}
                    className="w-full px-4 py-3 border border-white/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent bg-white/5 text-white placeholder-white/30"
                    placeholder=""
                  />
                </div>

                <div className="flex justify-center pt-4">
                  <button
                    type="submit"
                    className="px-16 py-3 rounded-full text-white transition-opacity hover:opacity-90 bg-[#4a6b82]"
                  >
                    Iniciar
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
