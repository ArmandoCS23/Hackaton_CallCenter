import logoImage from 'figma:asset/f0133992c7469b5e53a97efe8573c8c5576abf33.png';
import barImage from 'figma:asset/faf9fc94571f985b099904a6ff5ab23595393b95.png';

interface HeaderProps {
  currentPage: 'dashboard' | 'faq' | 'simulation';
  onNavigate: (page: 'dashboard' | 'faq' | 'simulation') => void;
  onLogout: () => void;
}

export default function Header({ currentPage, onNavigate, onLogout }: HeaderProps) {
  return (
    <header className="relative z-10">
      {/* Decorative Bar */}
      <div className="w-full h-16">
        <img src={barImage} alt="" className="w-full h-full object-cover" />
      </div>
      
      {/* Navigation */}
      <div className="px-8 py-4">
        <div className="flex items-center justify-between">
        {/* Logo */}
        <div className="flex-shrink-0">
          <img src={logoImage} alt="Aivox" className="h-10 object-contain" />
        </div>

        {/* Navigation */}
        <nav className="flex items-center gap-8">
          <button
            onClick={() => onNavigate('faq')}
            className={`text-white transition-opacity ${
              currentPage === 'faq' ? 'opacity-100' : 'opacity-70 hover:opacity-100'
            }`}
          >
            Preguntas Frecuentes
          </button>
          <button
            onClick={() => onNavigate('dashboard')}
            className={`text-white transition-opacity ${
              currentPage === 'dashboard' ? 'opacity-100' : 'opacity-70 hover:opacity-100'
            }`}
          >
            Registro de llamadas
          </button>
        </nav>

        {/* Logout Button */}
        <button
          onClick={onLogout}
          className="px-6 py-2 rounded-lg text-white transition-opacity hover:opacity-90 bg-[#8b1f1f]"
        >
          Cerrar Sesión
        </button>
        </div>
      </div>
    </header>
  );
}
