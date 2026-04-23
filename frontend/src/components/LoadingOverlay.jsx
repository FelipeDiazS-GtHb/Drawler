import React from 'react';

export default function LoadingOverlay({ isUploading, activeView }) {
  if (!isUploading) return null;
  
  return (
    <div className="loading-overlay">
      <div className="spinner"></div>
      <h2 className="loading-text">Procesando {activeView.title}...</h2>
      <p className="loading-subtext">Sincronizando información. Por favor, espera.</p>
    </div>
  );
}