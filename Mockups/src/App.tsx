import { useState } from 'react';
import LoginScreen from './components/LoginScreen';
import Dashboard from './components/Dashboard';
import FAQSection from './components/FAQSection';
import SimulationSection from './components/SimulationSection';

type Screen = 'login' | 'dashboard' | 'faq' | 'simulation';

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('login');

  return (
    <div className="min-h-screen bg-gray-50">
      {currentScreen === 'login' && (
        <LoginScreen onLogin={() => setCurrentScreen('dashboard')} />
      )}
      {currentScreen === 'dashboard' && (
        <Dashboard 
          onNavigateToFAQ={() => setCurrentScreen('faq')}
          onNavigateToSimulation={() => setCurrentScreen('simulation')}
          onLogout={() => setCurrentScreen('login')}
        />
      )}
      {currentScreen === 'faq' && (
        <FAQSection onBack={() => setCurrentScreen('dashboard')} />
      )}
      {currentScreen === 'simulation' && (
        <SimulationSection onBack={() => setCurrentScreen('dashboard')} />
      )}
    </div>
  );
}
