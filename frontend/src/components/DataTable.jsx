import React from 'react';

export default function DataTable({ activeView, isLoading, paginatedData, totalDataLength, pageSize, setPageSize, currentPage, setCurrentPage, totalPages, copyToClipboard }) {
  
  // BLINDAJE: Si activeView o las columnas no existen, no crasheamos la app.
  if (!activeView || !activeView.columns) {
    return <div className="content-wrapper"><p className="text-center mt-5">Configurando vista...</p></div>;
  }

  return (
    <div className="content-wrapper">
      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              {activeView.columns.map((col, idx) => (
                  <th key={idx} className={col.pinned ? 'sticky-col' : ''} style={{ minWidth: col.width }}>{col.field}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={activeView.columns.length} className="text-center">Cargando datos de la base de datos...</td></tr>
            ) : paginatedData?.length === 0 ? (
              <tr><td colSpan={activeView.columns.length} className="text-center">No hay registros para mostrar.</td></tr>
            ) : (
              paginatedData?.map((row, index) => (
                <tr key={index}>
                  {activeView.columns.map((col, colIdx) => (
                      <td 
                          key={colIdx} 
                          className={`cell-copy ${col.pinned ? 'sticky-col font-medium' : ''} ${col.mono ? 'font-mono' : ''} ${col.wrap ? 'cell-wrap' : ''}`} 
                          onClick={() => copyToClipboard(row[col.field])}
                      >
                          {row[col.field]}
                      </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="bottom-toolbar">
         <div className="status-text">Mostrando {paginatedData?.length || 0} de {totalDataLength || 0} registros</div>
         <div className="pagination-wrapper">
             <div className="view-controls">
                 <span className="view-label">Líneas:</span>
                 <select value={pageSize} onChange={(e) => { setPageSize(e.target.value === 'ALL' ? 'ALL' : Number(e.target.value)); setCurrentPage(1); }} className="select-page">
                     <option value={50}>50</option><option value={200}>200</option><option value="ALL">Todos</option>
                 </select>
             </div>
             {pageSize !== 'ALL' && totalPages > 1 && (
                 <div className="page-nav">
                     <button disabled={currentPage === 1} onClick={() => setCurrentPage(p => p - 1)} className="page-btn">Ant</button>
                     <span className="page-info">{currentPage} / {totalPages}</span>
                     <button disabled={currentPage === totalPages} onClick={() => setCurrentPage(p => p + 1)} className="page-btn">Sig</button>
                 </div>
             )}
         </div>
      </div>
    </div>
  );
}