import React, { useState, useEffect, useMemo } from 'react';

const API = "http://localhost:8000/api/control-interno";

function App() {
  const [seccion, setSeccion] = useState('NOTAS EYC');
  const [menuExpandido, setMenuExpandido] = useState('CONTROL_INTERNO');
  
  const [isNavOpen, setIsNavOpen] = useState(false);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  
  const [rowData, setRowData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const [pageSize, setPageSize] = useState(50);
  const [currentPage, setCurrentPage] = useState(1);
  const [colFilters, setColFilters] = useState({ CC_PACIENTE: '', CC_PROFESIONAL: '', SERVICIO: '', FECHA: '' });
  
  const [toast, setToast] = useState(null);

  const cargarDatos = async () => {
    setIsLoading(true);
    const res = await fetch(`${API}/data/${seccion}`);
    if (res.ok) setRowData(await res.json());
    setIsLoading(false);
    setCurrentPage(1); 
  };

  useEffect(() => { 
    cargarDatos(); 
    setShowActions(false);
  }, [seccion]);

  const filteredData = useMemo(() => {
    return rowData.filter(row => {
      const matchesCols = Object.keys(colFilters).every(key => {
        if (!colFilters[key]) return true;
        return String(row[key] || '').toLowerCase().includes(colFilters[key].toLowerCase());
      });
      return matchesCols;
    });
  }, [rowData, colFilters]);

  const paginatedData = useMemo(() => {
    if (pageSize === 'ALL') return filteredData;
    const start = (currentPage - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, currentPage, pageSize]);

  const totalPages = pageSize === 'ALL' ? 1 : Math.ceil(filteredData.length / pageSize);

  const handleFilterChange = (colId, value) => {
    setColFilters(prev => ({ ...prev, [colId]: value }));
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setColFilters({ CC_PACIENTE: '', CC_PROFESIONAL: '', SERVICIO: '', FECHA: '' });
    setCurrentPage(1);
  };

  // --- CARGUE ROBUSTO CON MANEJO DE ERRORES ---
  const handleFileUpload = async (tipo, e) => {
    const file = e.target.files[0];
    if (!file) return;
    setIsLoading(true);
    setShowActions(false);
    const fd = new FormData();
    fd.append("file", file);
    
    try {
        const res = await fetch(`${API}/upload/${seccion}/${tipo}`, { method: "POST", body: fd });
        if (!res.ok) {
            const errorData = await res.json();
            throw new Error(errorData.detail || "Error interno del servidor");
        }
        await cargarDatos();
        setToast(`✅ Archivo cargado correctamente.`);
        setTimeout(() => setToast(null), 3000);
    } catch (err) { 
        alert(`❌ Error al subir el archivo:\n${err.message}`); 
    } finally {
        setIsLoading(false);
        e.target.value = null; // Reiniciar el input siempre
    }
  };

  const getActionOptions = () => {
    switch(seccion) {
        case 'NOTAS EYC': return [{ label: 'Ventilados', tipo: 'ventilados' }, { label: 'Enfermería', tipo: 'enfermeria' }, { label: 'Act. Básicas', tipo: 'actividades' }];
        case 'MEDIOS INVASIVOS': return [{ label: 'Invasivos', tipo: 'invasivos' }];
        case 'RUTERO': return [{ label: 'Rutero', tipo: 'rutero' }];
        default: return [];
    }
  };

  const copyToClipboard = (text) => {
      if(!text) return;
      navigator.clipboard.writeText(text.toString());
      setToast(`Copiado: ${text}`);
      setTimeout(() => setToast(null), 2000);
  };

  const seleccionarSeccion = (nuevaSeccion) => {
      setSeccion(nuevaSeccion);
      setIsNavOpen(false); 
  };

  return (
    <div className="layout-container">
      
      {toast && <div className="toast-notification">{toast}</div>}

      <div className={`backdrop ${isNavOpen || isFilterOpen ? 'open' : ''}`} onClick={() => { setIsNavOpen(false); setIsFilterOpen(false); }}></div>

      {/* DRAWER IZQUIERDO: NAVEGACIÓN Y LOGO */}
      <aside className={`drawer left-drawer ${isNavOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <div className="brand-container">
             <img src="/logo.png" alt="Logo" className="brand-logo" onError={(e) => e.target.style.display = 'none'} />
             <div className="brand-text">
                 <span className="brand-title">MTD Auditoría</span>
                 <span className="brand-subtitle">Control Interno</span>
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

      {/* DRAWER DERECHO: FILTROS AVANZADOS */}
      <aside className={`drawer right-drawer ${isFilterOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <span className="drawer-title">FILTROS AVANZADOS</span>
          <button className="icon-btn no-border" onClick={() => setIsFilterOpen(false)}>
             <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
        <div className="drawer-body">
            <div className="filter-item">
                <label>Documento Paciente</label>
                <input type="text" value={colFilters.CC_PACIENTE} onChange={(e) => handleFilterChange('CC_PACIENTE', e.target.value)} />
            </div>
            <div className="filter-item">
                <label>ID Profesional</label>
                <input type="text" value={colFilters.CC_PROFESIONAL} onChange={(e) => handleFilterChange('CC_PROFESIONAL', e.target.value)} />
            </div>
            <div className="filter-item">
                <label>Fecha Específica</label>
                <input type="text" value={colFilters.FECHA} onChange={(e) => handleFilterChange('FECHA', e.target.value)} />
            </div>
            <div className="filter-item">
                <label>Servicio</label>
                <input type="text" value={colFilters.SERVICIO} onChange={(e) => handleFilterChange('SERVICIO', e.target.value)} />
            </div>
        </div>
        <div className="drawer-footer">
            <button className="btn-outline-full" onClick={clearFilters}>Limpiar Todo</button>
        </div>
      </aside>

      {/* CONTENIDO PRINCIPAL */}
      <main className="main-content">
        
        <header className="app-header">
            <div className="header-left">
                {/* ICONO DE HAMBURGUESA PARA MENÚ */}
                <button onClick={() => setIsNavOpen(true)} className="icon-btn border-btn">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
                </button>
                <div className="title-area">
                    <span className="path">{menuExpandido.replace('_', ' ')}</span>
                    <h1 className="current-page">{seccion}</h1>
                </div>
            </div>

            <div className="header-right">
                
                {/* ICONO DE EMBUDO PARA FILTROS */}
                <button onClick={() => setIsFilterOpen(true)} className={`icon-btn border-btn ${Object.values(colFilters).some(v => v !== '') ? 'active-filter' : ''}`} title="Filtrar columnas">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon></svg>
                </button>

                <div className="dropdown-container">
                    <button onClick={() => setShowActions(!showActions)} className="btn-primary">
                        Gestionar Data
                    </button>
                    {showActions && (
                        <div className="dropdown-menu">
                            <span className="dropdown-label">IMPORTAR</span>
                            {getActionOptions().map(opt => (
                                <div key={opt.tipo} className="dropdown-option">
                                    <span>Subir {opt.label}</span>
                                    <input type="file" accept=".csv" onChange={(e) => handleFileUpload(opt.tipo, e)} className="hidden-file" />
                                </div>
                            ))}
                            <div className="dropdown-divider"></div>
                            <button onClick={async () => { if(confirm(`¿Purgar sección?`)) { await fetch(`${API}/clear/${seccion}`, {method:'DELETE'}); cargarDatos(); setShowActions(false); } }} className="dropdown-option text-danger">
                                Purgar Datos
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </header>

        <div className="content-wrapper">
          
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th className="sticky-col" style={{ minWidth: '160px' }}>DOCUMENTO</th>
                  <th style={{ minWidth: '120px' }}>FECHA</th>
                  <th style={{ minWidth: '160px' }}>SERVICIO</th>
                  <th style={{ minWidth: '400px' }}>REGISTRO CLÍNICO</th>
                  <th style={{ minWidth: '150px' }}>ID PROF.</th>
                  <th style={{ minWidth: '250px' }}>UBICACIÓN GPS</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan="6" className="text-center">Sincronizando datos...</td></tr>
                ) : paginatedData.length === 0 ? (
                  <tr><td colSpan="6" className="text-center">No hay registros que coincidan con los filtros.</td></tr>
                ) : (
                  paginatedData.map((row, index) => (
                    <tr key={index}>
                      <td className="sticky-col cell-copy font-mono font-medium" onClick={() => copyToClipboard(row.CC_PACIENTE)}>
                        {row.CC_PACIENTE}
                      </td>
                      <td className="text-muted">{row.FECHA}</td>
                      <td>{row.SERVICIO}</td>
                      <td className="cell-wrap cell-copy" onClick={() => copyToClipboard(row.DETALLE)}>{row.TURNO || row.DETALLE}</td>
                      <td className="cell-copy font-mono" onClick={() => copyToClipboard(row.CC_PROFESIONAL)}>{row.CC_PROFESIONAL}</td>
                      <td className="text-muted text-sm">{row.GEOREFERENCIA}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="bottom-toolbar">
             <div className="status-text">
                 Mostrando {paginatedData.length} de {filteredData.length} registros
             </div>
             
             <div className="pagination-wrapper">
                 <div className="view-controls">
                     <span className="view-label">Líneas por página:</span>
                     <select value={pageSize} onChange={(e) => { setPageSize(e.target.value === 'ALL' ? 'ALL' : Number(e.target.value)); setCurrentPage(1); }} className="select-page">
                         <option value={50}>50</option>
                         <option value={200}>200</option>
                         <option value="ALL">Todos</option>
                     </select>
                 </div>

                 {pageSize !== 'ALL' && totalPages > 1 && (
                     <div className="page-nav">
                         <button disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)} className="page-btn">Anterior</button>
                         <span className="page-info">{currentPage} / {totalPages}</span>
                         <button disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)} className="page-btn">Siguiente</button>
                     </div>
                 )}
             </div>
          </div>

        </div>
      </main>

      <style>{`
        body { margin: 0; font-family: 'Poppins', sans-serif; background-color: #ffffff; color: #334155; }
        
        .layout-container { display: flex; height: 100vh; overflow: hidden; position: relative; }
        .main-content { flex: 1; display: flex; flex-direction: column; width: 100%; }
        .content-wrapper { flex: 1; display: flex; flex-direction: column; padding: 24px 32px; background: #ffffff; overflow: hidden; }

        .backdrop { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.15); z-index: 90; opacity: 0; pointer-events: none; transition: 0.2s; }
        .backdrop.open { opacity: 1; pointer-events: auto; }
        .drawer { position: fixed; top: 0; height: 100vh; width: 280px; background: #ffffff; z-index: 100; display: flex; flex-direction: column; transition: transform 0.3s ease; box-shadow: 0 0 15px rgba(0,0,0,0.05); }
        .left-drawer { left: 0; transform: translateX(-100%); border-right: 1px solid #e2e8f0; }
        .left-drawer.open { transform: translateX(0); }
        .right-drawer { right: 0; transform: translateX(100%); border-left: 1px solid #e2e8f0; }
        .right-drawer.open { transform: translateX(0); }

        /* HEADER DEL MENU (CON LOGO) */
        .drawer-header { padding: 20px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
        .brand-container { display: flex; align-items: center; gap: 10px; }
        .brand-logo { height: 32px; width: auto; object-fit: contain; }
        .brand-text { display: flex; flex-direction: column; }
        .brand-title { font-size: 15px; font-weight: 700; color: #0f172a; margin: 0; letter-spacing: -0.5px; }
        .brand-subtitle { font-size: 10px; color: #64748b; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; }

        .drawer-title { font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.05em; }
        .drawer-body { padding: 16px; flex: 1; overflow-y: auto; }
        .drawer-footer { padding: 16px; border-top: 1px solid #f1f5f9; }

        .app-header { height: 64px; padding: 0 32px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; }
        .header-left, .header-right { display: flex; align-items: center; gap: 16px; }
        .title-area { display: flex; flex-direction: column; }
        .path { font-size: 10px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 2px; }
        .current-page { font-size: 16px; font-weight: 600; color: #0f172a; margin: 0; }

        /* ICONOS SVG */
        .icon-btn { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: transparent; border: 1px solid transparent; border-radius: 6px; color: #475569; cursor: pointer; transition: 0.15s; }
        .icon-btn:hover { background: #f1f5f9; color: #0f172a; }
        .border-btn { border: 1px solid #e2e8f0; }
        .no-border { border: none; }
        .active-filter { background: #eff6ff; border-color: #3b82f6; color: #3b82f6; }

        .btn-primary { background: #0f172a; color: #ffffff; border: none; padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 500; cursor: pointer; transition: 0.2s; font-family: 'Poppins', sans-serif; }
        .btn-primary:hover { background: #1e293b; }
        .btn-outline-full { width: 100%; background: transparent; border: 1px solid #cbd5e1; color: #475569; padding: 8px; border-radius: 6px; font-size: 12px; font-weight: 500; cursor: pointer; font-family: 'Poppins', sans-serif; }

        /* =========================================
           TABLA SCROLL HORIZONTAL MULTI-COLUMNA 
           ========================================= */
        .table-container { 
            flex: 1; 
            overflow: auto; 
            border: 1px solid #e2e8f0; 
            border-radius: 8px 8px 0 0; 
            border-bottom: none; 
            background: #ffffff;
        }
        
        .custom-table { 
            width: 100%; 
            min-width: 1200px; 
            border-collapse: separate; 
            border-spacing: 0; 
            text-align: left; 
        }

        .custom-table thead th { 
            position: sticky; 
            top: 0; 
            background-color: #f8fafc; 
            color: #64748b; 
            font-size: 11px; 
            font-weight: 600; 
            text-transform: uppercase; 
            padding: 12px 16px; 
            border-bottom: 1px solid #e2e8f0; 
            z-index: 10; 
        }

        .sticky-col {
            position: sticky;
            left: 0;
            background-color: #ffffff;
            z-index: 5;
            box-shadow: inset -1px 0 0 #e2e8f0; 
        }
        
        .custom-table thead th.sticky-col {
            z-index: 20; 
            background-color: #f8fafc;
        }

        .custom-table tbody tr { background-color: #ffffff; transition: 0.15s; }
        .custom-table tbody td { padding: 12px 16px; font-size: 13px; color: #334155; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
        
        .custom-table tbody tr:hover, 
        .custom-table tbody tr:hover .sticky-col { 
            background-color: #f8fafc; 
        }
        
        .cell-wrap { white-space: pre-wrap; word-break: break-word; line-height: 1.5; }
        .cell-copy { cursor: pointer; transition: color 0.1s; }
        .cell-copy:hover { color: #3b82f6; }
        .font-mono { font-family: ui-monospace, Consolas, monospace; }
        .font-medium { font-weight: 500; color: #0f172a; }
        .text-muted { color: #64748b; }
        .text-sm { font-size: 12px; }
        .text-center { text-align: center; padding: 40px !important; color: #94a3b8; }

        .bottom-toolbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px; }
        .status-text { font-size: 12px; color: #64748b; font-weight: 500; }
        .pagination-wrapper { display: flex; align-items: center; gap: 24px; }
        .view-controls { display: flex; align-items: center; gap: 8px; }
        .view-label { font-size: 12px; color: #64748b; }
        .select-page { padding: 4px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 12px; color: #0f172a; outline: none; background: #ffffff; cursor: pointer; font-family: 'Poppins', sans-serif; }
        
        .page-nav { display: flex; align-items: center; gap: 12px; }
        .page-btn { background: transparent; border: 1px solid #e2e8f0; padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 500; color: #0f172a; cursor: pointer; transition: 0.15s; font-family: 'Poppins', sans-serif; }
        .page-btn:hover:not(:disabled) { background: #f1f5f9; }
        .page-btn:disabled { color: #94a3b8; cursor: not-allowed; border-color: #f1f5f9; }
        .page-info { font-size: 12px; color: #475569; font-weight: 500; }

        .toast-notification { position: fixed; bottom: 24px; right: 24px; background: #0f172a; color: white; padding: 10px 20px; border-radius: 6px; font-size: 13px; font-weight: 500; z-index: 1000; box-shadow: 0 4px 6px rgba(0,0,0,0.1); animation: fadeUp 0.2s ease-out; }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        .dropdown-container { position: relative; }
        .dropdown-menu { position: absolute; top: calc(100% + 4px); right: 0; width: 180px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); padding: 6px; z-index: 50; }
        .dropdown-label { display: block; font-size: 10px; font-weight: 600; color: #94a3b8; padding: 4px 8px; margin-bottom: 2px; }
        .dropdown-option { position: relative; display: block; width: 100%; text-align: left; padding: 8px; background: transparent; border: none; border-radius: 4px; font-size: 13px; color: #334155; cursor: pointer; font-family: 'Poppins', sans-serif; }
        .dropdown-option:hover { background: #f1f5f9; }
        .text-danger { color: #dc2626; }
        .text-danger:hover { background: #fef2f2; color: #b91c1c; }
        .dropdown-divider { height: 1px; background: #e2e8f0; margin: 4px 0; }
        .hidden-file { position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }

        .menu-group { margin-bottom: 4px; }
        .menu-trigger { width: 100%; display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: transparent; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 500; color: #334155; font-family: 'Poppins', sans-serif; transition: 0.2s; }
        .menu-trigger:hover { background: #f8fafc; }
        .menu-arrow { color: #94a3b8; transition: transform 0.2s; }
        .menu-content { display: flex; flex-direction: column; gap: 2px; padding-left: 12px; margin-top: 2px; }
        .menu-item { text-align: left; padding: 8px 12px; border-radius: 6px; border: none; background: transparent; color: #64748b; font-size: 13px; cursor: pointer; font-family: 'Poppins', sans-serif; transition: 0.15s; }
        .menu-item:hover { color: #0f172a; background: #f1f5f9; }
        .menu-item.active { background: #f1f5f9; color: #0f172a; font-weight: 500; }
        
        .filter-item { margin-bottom: 16px; }
        .filter-item label { display: block; font-size: 11px; font-weight: 500; color: #64748b; margin-bottom: 6px; }
        .filter-item input { width: 100%; padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; font-family: 'Poppins', sans-serif; outline: none; transition: 0.15s; }
        .filter-item input:focus { border-color: #0f172a; }
      `}</style>
    </div>
  );
}

export default App;