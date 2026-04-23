import React, { useState } from 'react';

export default function Header({ setIsNavOpen, setIsFilterOpen, activeView, colFilters, handleFileUpload, handleDownloadTemplate, handleClearData }) {
  const [showActions, setShowActions] = useState(false);

  return (
    <header className="app-header">
      <div className="header-left">
          <button onClick={() => setIsNavOpen(true)} className="icon-btn border-btn">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
          </button>
          <div className="title-area">
              <span className="path">{activeView.parent.replace('_', ' ')}</span>
              <h1 className="current-page">{activeView.title}</h1>
          </div>
      </div>

      <div className="header-right">
          <button onClick={() => setIsFilterOpen(true)} className={`icon-btn border-btn ${Object.values(colFilters).some(v => v !== '') ? 'active-filter' : ''}`} title="Filtros">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
          </button>

          <div className="dropdown-container">
              <button onClick={() => setShowActions(!showActions)} className="btn-primary">
                  Gestionar Data
              </button>
              
              {showActions && (
                  <div className="dropdown-menu">
                      {activeView.templateUrl && (
                          <>
                              <span className="dropdown-label">PLANTILLAS</span>
                              <button onClick={() => { handleDownloadTemplate(); setShowActions(false); }} className="dropdown-option" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></svg>
                                  Bajar Plantilla
                              </button>
                              <div className="dropdown-divider"></div>
                          </>
                      )}
                      
                      {activeView.uploadOptions.length > 0 && (
                          <>
                              <span className="dropdown-label">IMPORTAR</span>
                              {activeView.uploadOptions.map(opt => (
                                  <div key={opt.tipo} className="dropdown-option">
                                      <span>Subir {opt.label}</span>
                                      <input type="file" accept=".csv" onChange={(e) => { handleFileUpload(opt.tipo, e); setShowActions(false); }} className="hidden-file" />
                                  </div>
                              ))}
                              <div className="dropdown-divider"></div>
                          </>
                      )}
                      
                      <button onClick={() => { handleClearData(); setShowActions(false); }} className="dropdown-option text-danger">
                          Purgar Datos
                      </button>
                  </div>
              )}
          </div>
      </div>
    </header>
  );
}