import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

// Importar Poppins desde Google Fonts
const globalStyles = `
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  body {
    /* Cambio a Poppins como fuente principal */
    font-family: 'Poppins', -apple-system, sans-serif; 
    background-color: #ffffff;
    color: #334155;
    -webkit-font-smoothing: antialiased;
  }
  button, input, select {
    font-family: inherit;
  }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
  ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
`;

const styleSheet = document.createElement("style");
styleSheet.innerText = globalStyles;
document.head.appendChild(styleSheet);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)