import React, { useState } from 'react';

export default function Sidebar({ isNavOpen, setIsNavOpen, seccion, setSeccion }) {
  const [menuExpandido, setMenuExpandido] = useState('CONTROL_INTERNO');

  const seleccionarSeccion = (nuevaSeccion) => {
    setSeccion(nuevaSeccion);
    setIsNavOpen(false);
  };

  return (
    <aside className={`drawer left-drawer ${isNavOpen ? 'open' : ''}`}>
      <div className="drawer-header">
        <div className="brand-container">
           <img src="/logo.png" alt="Logo" className="brand-logo" onError={(e) => e.target.style.display = 'none'} />
           <div className="brand-text">
               <span className="brand-title">MTD Auditoría</span>
               <span className="brand-subtitle">Plataforma Core</span>
           </div>
        </div>
        <button className="icon-btn no-border" onClick={() => setIsNavOpen(false)}>
           <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>
      
      <nav className="drawer-body">
          <div className={`menu-group ${menuExpandido === 'CONTROL_INTERNO' ? 'expanded' : ''}`}>
              <button className="menu-trigger" onClick={() => setMenuExpandido(menuExpandido === 'CONTROL_INTERNO' ? '' : 'CONTROL_INTERNO')}>
                  <span>Control Interno</span>
                  <svg className="menu-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ transform: menuExpandido === 'CONTROL_INTERNO' ? 'rotate(180deg)' : 'rotate(0deg)' }}><polyline points="6 9 12 15 18 9"></polyline></svg>
              </button>
              {menuExpandido === 'CONTROL_INTERNO' && (
                  <div className="menu-content">
                      <button className={`menu-item ${seccion === 'NOTAS EYC' ? 'active' : ''}`} onClick={() => seleccionarSeccion('NOTAS EYC')}>Notas EYC</button>
                      <button className={`menu-item ${seccion === 'MEDIOS INVASIVOS' ? 'active' : ''}`} onClick={() => seleccionarSeccion('MEDIOS INVASIVOS')}>Medios Invasivos</button>
                      <button className={`menu-item ${seccion === 'RUTERO' ? 'active' : ''}`} onClick={() => seleccionarSeccion('RUTERO')}>Rutero</button>
                  </div>
              )}
          </div>
          <div className={`menu-group ${menuExpandido === 'CUENTAS_MEDICAS' ? 'expanded' : ''}`}>
              <button className="menu-trigger" onClick={() => setMenuExpandido(menuExpandido === 'CUENTAS_MEDICAS' ? '' : 'CUENTAS_MEDICAS')}>
                  <span>Cuentas Médicas</span>
                  <svg className="menu-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ transform: menuExpandido === 'CUENTAS_MEDICAS' ? 'rotate(180deg)' : 'rotate(0deg)' }}><polyline points="6 9 12 15 18 9"></polyline></svg>
              </button>
              {menuExpandido === 'CUENTAS_MEDICAS' && (
                  <div className="menu-content">
                      <button className={`menu-item ${seccion === 'FACTURACION' ? 'active' : ''}`} onClick={() => seleccionarSeccion('FACTURACION')}>Facturación</button>
                      <button className={`menu-item ${seccion === 'GLOSAS' ? 'active' : ''}`} onClick={() => seleccionarSeccion('GLOSAS')}>Glosas</button>
                  </div>
              )}
          </div>
      </nav>
    </aside>
  );
}