export const API = "http://localhost:8000/api/control-interno";

export const VIEW_CONFIG = {
    'NOTAS EYC': {
        parent: 'CONTROL INTERNO',
        title: 'Notas EYC',
        templateUrl: '/template/eyc',
        uploadOptions: [{ label: 'Data EYC (Plantilla)', tipo: 'eyc', endpoint: '/upload/eyc' }],
        dataEndpoint: '/data/eyc',
        clearEndpoint: '/clear/eyc',
        filters: [
            { id: 'CC PACIENTE', label: 'Documento Paciente' },
            { id: 'CC PROFESIONAL', label: 'Documento Profesional' },
            { id: 'FECHA', label: 'Fecha Específica' },
            { id: 'SERVICIO', label: 'Servicio / Tipo' }
        ],
        columns: [
            { field: 'CC PROFESIONAL', width: '150px', mono: true, pinned: true },
            { field: 'SERVICIO', width: '150px' },
            { field: 'FECHA', width: '120px' },
            { field: 'CC PACIENTE', width: '150px', mono: true },
            { field: 'TURNO', width: '120px', wrap: true },
            { field: 'FECHA CREACION', width: '160px' },
            { field: 'LIDER', width: '120px' },
            { field: 'COORDINADOR', width: '120px' },
            { field: 'GEOREFERENCIA', width: '250px' },
            { field: 'ESTADO', width: '120px' },
            { field: 'CRUCE', width: '120px' },
            { field: 'EPS', width: '150px' },
            { field: 'DIFERENCIADOR', width: '150px' }
        ]
    },
    'MEDIOS INVASIVOS': {
        parent: 'CONTROL INTERNO',
        title: 'Medios Invasivos',
        templateUrl: '/template/invasivos', // <--- Habilitamos el botón "Bajar Plantilla"
        uploadOptions: [{ label: 'Data Invasivos (Plantilla)', tipo: 'invasivos', endpoint: '/upload/invasivos' }],
        dataEndpoint: '/data/invasivos',
        clearEndpoint: '/clear/invasivos',
        filters: [
            { id: 'CC PACIENTE', label: 'Documento Paciente' },
            { id: 'CC PROFESIONAL', label: 'Documento Profesional' },
            { id: 'FECHA', label: 'Fecha Específica' },
            { id: 'JORNADA', label: 'Jornada' },
            { id: 'ESTADO', label: 'Estado' }
        ],
        columns: [
            { field: 'CC PROFESIONAL', width: '150px', mono: true, pinned: true },
            { field: 'FECHA', width: '120px' },
            { field: 'CC PACIENTE', width: '150px', mono: true },
            { field: 'JORNADA', width: '400px', wrap: true },
            { field: 'FECHA CREACION', width: '160px' },
            { field: 'LIDER', width: '120px' },
            { field: 'COORDINADOR', width: '120px' },
            { field: 'GEOREFERENCIA', width: '250px' },
            { field: 'ESTADO', width: '120px' },
            { field: 'CRUCE', width: '120px' }

        ]
    },
    'RUTERO': {
        parent: 'CONTROL INTERNO',
        title: 'Rutero',
        templateUrl: null,
        uploadOptions: [{ label: 'Rutero', tipo: 'rutero', endpoint: '/upload/rutero' }],
        dataEndpoint: '/data/rutero',
        clearEndpoint: '/clear/rutero',
        filters: [
            { id: 'DOCUMENTO PACIENTE', label: 'Documento Paciente' },
            { id: 'DOCUMENTO PROFESIONAL', label: 'Documento Profesional' },
            { id: 'FECHA', label: 'Fecha Específica' },
            { id: 'TIPO', label: 'Tipo' }
        ],
        columns: [
            { field: 'FECHA', width: '120px', pinned: true },
            { field: 'DOCUMENTO PROFESIONAL', width: '180px', mono: true },
            { field: 'PROFESIONAL', width: '250px' },
            { field: 'ASUNTO', width: '350px', wrap: true },
            { field: 'DOCUMENTO PACIENTE', width: '180px', mono: true },
            { field: 'PACIENTE', width: '250px' },
            { field: 'TIPO', width: '200px' },
            { field: 'ESTADO', width: '120px' }
        ]
    },
    'FACTURACION': {
        parent: 'CUENTAS MEDICAS',
        title: 'Facturación',
        templateUrl: null,
        uploadOptions: [],
        dataEndpoint: '/data/facturacion',
        clearEndpoint: '/clear/facturacion',
        filters: [],
        columns: []
    },
    'GLOSAS': {
        parent: 'CUENTAS MEDICAS',
        title: 'Glosas',
        templateUrl: null,
        uploadOptions: [],
        dataEndpoint: '/data/glosas',
        clearEndpoint: '/clear/glosas',
        filters: [],
        columns: []
    }
};