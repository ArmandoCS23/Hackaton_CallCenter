import BackgroundPattern from './BackgroundPattern';
import Header from './Header';

interface FAQSectionProps {
  onBack: () => void;
}

export default function FAQSection({ onBack }: FAQSectionProps) {
  const handleNavigate = (page: 'dashboard' | 'faq' | 'simulation') => {
    if (page === 'dashboard') onBack();
    // Otras navegaciones se manejarían aquí
  };

  const faqContent = [
    {
      pregunta: '¿Cómo puedo registrar una nueva llamada?',
      respuesta: 'Para registrar una nueva llamada, dirígete al dashboard principal y haz clic en el botón "Nueva Llamada". Completa los campos requeridos como tipo de llamada, número, cliente y agente.',
    },
    {
      pregunta: '¿Qué tipos de llamadas se pueden registrar?',
      respuesta: 'El sistema permite registrar dos tipos de llamadas: Entrantes (llamadas recibidas) y Salientes (llamadas realizadas).',
    },
    {
      pregunta: '¿Cómo exporto el registro de llamadas?',
      respuesta: 'Puedes exportar las llamadas utilizando el botón "Exportar" ubicado en la parte inferior de la sección de preguntas frecuentes.',
    },
    {
      pregunta: '¿Para qué sirve la función de Simulación?',
      respuesta: 'La función de Simulación te permite practicar y ensayar interacciones entre agentes y clientes antes de realizar llamadas reales.',
    },
  ];

  return (
    <div className="min-h-screen relative">
      <BackgroundPattern />
      
      <div className="relative z-10">
        <Header 
          currentPage="faq" 
          onNavigate={handleNavigate}
          onLogout={() => {}}
        />

        {/* Main Content */}
        <main className="px-8 py-12">
          <div className="max-w-5xl mx-auto">
            {/* Title */}
            <h1 className="text-white mb-12 text-[4.25rem] leading-[1.05] text-center">
              Preguntas Frecuentes
            </h1>

            {/* Preguntas Frecuentes - Estáticas */}
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 border border-white/20 mb-8 min-h-[200px]">
              <ul className="space-y-6">
                <li>
                  <strong className="text-white">¿Cómo se calculan las fracciones?</strong>
                  <p className="text-white/70 mt-2">Para sumar fracciones con distinto denominador, encuentra un denominador común, ajusta los numeradores y suma. Puedo darte un ejemplo si quieres.</p>
                </li>
                <li>
                  <strong className="text-white">¿Cómo se calcula el área de un rectángulo?</strong>
                  <p className="text-white/70 mt-2">Multiplica la base por la altura: área = base × altura.</p>
                </li>
                <li>
                  <strong className="text-white">¿Qué son los números primos?</strong>
                  <p className="text-white/70 mt-2">Un número primo es aquel mayor que 1 que solo tiene dos divisores: 1 y él mismo.</p>
                </li>
                <li>
                  <strong className="text-white">¿Cómo me preparo para un examen?</strong>
                  <p className="text-white/70 mt-2">Haz un plan de estudio, repasa ejercicios con tiempo, y duerme bien la noche anterior. Puedo sugerir un plan si me dices la materia.</p>
                </li>
              </ul>
            </div>

            {/* Export Button removed as requested */}
          </div>
        </main>
      </div>
    </div>
  );
}
