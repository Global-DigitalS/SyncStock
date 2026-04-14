import React, { createContext, useContext, useState, useCallback } from 'react';

const SyncProgressContext = createContext();

export const SYNC_STEPS = {
  supplier: [
    "Conectando con la fuente",
    "Descargando archivo",
    "Procesando datos",
    "Guardando productos"
  ],
  store: [
    "Obteniendo catálogo",
    "Actualizando precios y stock",
    "Verificando resultados"
  ],
  woocommerce: [
    "Obteniendo catálogo",
    "Actualizando WooCommerce",
    "Verificando resultados"
  ],
  export: [
    "Preparando catálogo",
    "Exportando productos",
    "Finalizando"
  ],
};

export function SyncProgressProvider({ children }) {
  const [operations, setOperations] = useState([]);

  const startSync = useCallback((id, title, steps) => {
    setOperations(prev => [...prev, {
      id,
      title,
      steps,
      currentStepIndex: 0,
      progress: 0,
      status: 'running', // 'running' | 'done' | 'error'
      message: steps[0] || 'Iniciando...',
    }]);
  }, []);

  const advanceStep = useCallback((id, stepIndex) => {
    setOperations(prev => prev.map(op =>
      op.id === id
        ? { ...op, currentStepIndex: stepIndex }
        : op
    ));
  }, []);

  const setProgress = useCallback((id, progress, message) => {
    setOperations(prev => prev.map(op => {
      if (op.id !== id) return op;

      // Auto-advance step based on progress percentage
      let stepIndex = op.currentStepIndex;
      const stepSize = 100 / (op.steps.length - 1);
      const nextStep = Math.floor(progress / stepSize);
      if (nextStep > stepIndex && nextStep < op.steps.length) {
        stepIndex = nextStep;
      }

      return {
        ...op,
        progress,
        message,
        currentStepIndex: stepIndex,
      };
    }));
  }, []);

  const completeSync = useCallback((id, summary) => {
    setOperations(prev => prev.map(op =>
      op.id === id
        ? {
            ...op,
            status: 'done',
            progress: 100,
            currentStepIndex: op.steps.length - 1,
            message: summary || 'Completado',
          }
        : op
    ));

    // Auto-dismiss after 5 seconds
    setTimeout(() => dismissSync(id), 5000);
  }, []);

  const failSync = useCallback((id, error) => {
    setOperations(prev => prev.map(op =>
      op.id === id
        ? {
            ...op,
            status: 'error',
            message: error || 'Error desconocido',
          }
        : op
    ));

    // Auto-dismiss after 8 seconds for errors
    setTimeout(() => dismissSync(id), 8000);
  }, []);

  const dismissSync = useCallback((id) => {
    setOperations(prev => prev.filter(op => op.id !== id));
  }, []);

  const value = {
    operations,
    startSync,
    advanceStep,
    setProgress,
    completeSync,
    failSync,
    dismissSync,
  };

  return (
    <SyncProgressContext.Provider value={value}>
      {children}
    </SyncProgressContext.Provider>
  );
}

export function useSyncProgress() {
  const context = useContext(SyncProgressContext);
  if (!context) {
    throw new Error('useSyncProgress debe ser usado dentro de SyncProgressProvider');
  }
  return context;
}
