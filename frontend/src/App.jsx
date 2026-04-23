import React, { useState, useEffect, useMemo } from 'react';
import { API, VIEW_CONFIG } from './config/viewsConfig';
import Sidebar from './components/Sidebar';
import FilterDrawer from './components/FilterDrawer';
import Header from './components/Header';
import DataTable from './components/DataTable';
import LoadingOverlay from './components/LoadingOverlay';
import './App.css';

export default function App() {
  const [seccion, setSeccion] = useState('NOTAS EYC');
  const [isNavOpen, setIsNavOpen] = useState(false);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  
  const [rowData, setRowData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false); 
  
  const [pageSize, setPageSize] = useState(50);
  const [currentPage, setCurrentPage] = useState(1);
  const [colFilters, setColFilters] = useState({});
  const [toast, setToast] = useState(null);

  // Aseguramos siempre tener una vista activa válida
  const activeView = VIEW_CONFIG[seccion] || VIEW_CONFIG['NOTAS EYC'];

  // =================================================================
  // FIX: AHORA USA EL ENDPOINT ESPECÍFICO DEL DICCIONARIO
  // =================================================================
  const cargarDatos = async () => {
    if (!activeView.dataEndpoint) return; // Si la vista no tiene endpoint, no hace nada

    setIsLoading(true);
    try {
      // Llamada dinámica: Ya no usa /data/NOTAS EYC, ahora usa /data/eyc
      const res = await fetch(`${API}${activeView.dataEndpoint}`);
      if (res.ok) {
        const data = await res.json();
        setRowData(Array.isArray(data) ? data : []);
      } else {
        setRowData([]);
      }
    } catch (e) {
      console.error("Error al cargar datos:", e);
      setRowData([]);
    }
    setIsLoading(false);
    setCurrentPage(1); 
  };

  useEffect(() => { 
    cargarDatos(); 
    setColFilters({}); 
  }, [seccion]);

  const filteredData = useMemo(() => {
    if (!Array.isArray(rowData)) return [];
    return rowData.filter(row => {
      return Object.keys(colFilters).every(key => {
        if (!colFilters[key]) return true;
        return String(row[key] || '').toLowerCase().includes(colFilters[key].toLowerCase());
      });
    });
  }, [rowData, colFilters]);

  const paginatedData = useMemo(() => {
    if (pageSize === 'ALL') return filteredData;
    const start = (currentPage - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, currentPage, pageSize]);

  const totalPages = pageSize === 'ALL' ? 1 : Math.ceil(filteredData.length / pageSize);

  const handleFileUpload = async (tipo, e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setIsUploading(true); 
    const fd = new FormData();
    fd.append("file", file);
    
    // FIX: Busca la URL correcta en las opciones de subida de la configuración
    const uploadOption = activeView.uploadOptions.find(opt => opt.tipo === tipo);
    const url = uploadOption ? `${API}${uploadOption.endpoint}` : `${API}/upload/${seccion}/${tipo}`;

    try {
        const res = await fetch(url, { method: "POST", body: fd });
        if (!res.ok) throw new Error("Error en servidor");
        await cargarDatos();
        mostrarToast(`✅ Archivo de ${activeView.title} procesado con éxito.`);
    } catch (err) { 
        alert("Error al subir archivo. Asegúrate de usar el formato correcto."); 
    } finally { 
        setIsUploading(false); 
    }
  };

  const handleClearData = async () => {
    if(window.confirm(`¿Estás seguro de purgar todos los datos de ${activeView?.title}?`)) { 
      // FIX: Llama a la ruta de borrado limpia, ej: /clear/eyc
      await fetch(`${API}${activeView.clearEndpoint}`, {method:'DELETE'}); 
      cargarDatos(); 
    }
  };

  const mostrarToast = (msg) => {
      setToast(msg);
      setTimeout(() => setToast(null), 3000);
  };

  const copyToClipboard = (text) => {
      if(!text) return;
      navigator.clipboard.writeText(text.toString());
      mostrarToast(`Copiado: ${text}`);
  };

  return (
    <div className="layout-container">
      <LoadingOverlay isUploading={isUploading} activeView={activeView} />
      
      {toast && <div className="toast-notification">{toast}</div>}

      <div className={`backdrop ${isNavOpen || isFilterOpen ? 'open' : ''}`} onClick={() => { setIsNavOpen(false); setIsFilterOpen(false); }}></div>

      <Sidebar 
        isNavOpen={isNavOpen} setIsNavOpen={setIsNavOpen} 
        seccion={seccion} setSeccion={setSeccion} 
      />
      
      <FilterDrawer 
        isFilterOpen={isFilterOpen} setIsFilterOpen={setIsFilterOpen} 
        activeView={activeView} colFilters={colFilters} 
        handleFilterChange={(id, val) => { setColFilters(prev => ({ ...prev, [id]: val })); setCurrentPage(1); }} 
        clearFilters={() => { setColFilters({}); setCurrentPage(1); }} 
      />

      <main className="main-content">
        <Header 
          setIsNavOpen={setIsNavOpen} setIsFilterOpen={setIsFilterOpen} 
          activeView={activeView} colFilters={colFilters} 
          handleFileUpload={handleFileUpload} handleClearData={handleClearData}
          handleDownloadTemplate={() => { if(activeView?.templateUrl) window.open(`${API}${activeView.templateUrl}`, "_blank"); }}
        />
        <DataTable 
          activeView={activeView} isLoading={isLoading} paginatedData={paginatedData} 
          totalDataLength={filteredData.length} pageSize={pageSize} setPageSize={setPageSize} 
          currentPage={currentPage} setCurrentPage={setCurrentPage} 
          totalPages={totalPages} copyToClipboard={copyToClipboard}
        />
      </main>
    </div>
  );
}