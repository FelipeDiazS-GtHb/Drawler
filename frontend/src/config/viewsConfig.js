export const API = "http://localhost:8000/api/control-interno";

export const VIEW_CONFIG = {
  'NOTAS EYC': {
    parent: 'CONTROL INTERNO', title: 'Notas EYC', templateUrl: '/template/eyc',
    uploadOptions: [{ label: 'Data EYC (Plantilla)', endpoint: '/upload/eyc' }],
    dataEndpoint: '/data/eyc', clearEndpoint: '/clear/eyc', // <- RUTAS ESPECÍFICAS
    filters: [ /*Tus filtros de EYC*/ ], columns: [ /* Tus columnas EYC */ ]
  },
  'MEDIOS INVASIVOS': {
    parent: 'CONTROL INTERNO', title: 'Medios Invasivos', templateUrl: null,
    uploadOptions: [{ label: 'Invasivos', endpoint: '/upload/invasivos' }],
    dataEndpoint: '/data/invasivos', clearEndpoint: '/clear/invasivos', // <- RUTAS ESPECÍFICAS
    filters: [ /*Tus filtros de Invasivos*/ ], columns: [ /* Tus columnas Invasivos */ ]
  },
  'RUTERO': {
    parent: 'CONTROL INTERNO', title: 'Rutero', templateUrl: null,
    uploadOptions: [{ label: 'Rutero', endpoint: '/upload/rutero' }],
    dataEndpoint: '/data/rutero', clearEndpoint: '/clear/rutero', // <- RUTAS ESPECÍFICAS
    filters: [ /*Tus filtros de Rutero*/ ], columns: [ /* Tus columnas Rutero */ ]
  }
};