import React from 'react';

export default function FilterDrawer({ isFilterOpen, setIsFilterOpen, activeView, colFilters, handleFilterChange, clearFilters }) {
  return (
    <aside className={`drawer right-drawer ${isFilterOpen ? 'open' : ''}`}>
      <div className="drawer-header">
        <span className="drawer-title">FILTROS {activeView.title.toUpperCase()}</span>
        <button className="icon-btn no-border" onClick={() => setIsFilterOpen(false)}>
           <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
      </div>
      <div className="drawer-body">
          {activeView.filters.length > 0 ? (
             activeView.filters.map(filter => (
               <div key={filter.id} className="filter-item">
                   <label>{filter.label}</label>
                   <input type="text" value={colFilters[filter.id] || ''} onChange={(e) => handleFilterChange(filter.id, e.target.value)} />
               </div>
             ))
          ) : (
             <p className="text-center" style={{fontSize: '12px', color: '#94a3b8'}}>Sin filtros para esta sección.</p>
          )}
      </div>
      <div className="drawer-footer">
          <button className="btn-outline-full" onClick={clearFilters}>Limpiar Todo</button>
      </div>
    </aside>
  );
}