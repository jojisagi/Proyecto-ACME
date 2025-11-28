# Project Structure

## Organization Principles

- **src/**: Todo el código ejecutable (Lambdas, lógica de negocio, utilidades)
- **iac/**: Toda la infraestructura como código (CloudFormation)
- **data/**: Datos de prueba y ejemplos (JSON, CSV, imágenes)
- Separar handlers de Lambda de la lógica de negocio
- Usar variables de entorno para configuración (no hardcodear)

## Folder Structure

```
.
├── .kiro/                      # Kiro configuration
│   └── steering/               # AI assistant guidance
├── src/                        # CÓDIGO EJECUTABLE
│   ├── lambdas/                # Funciones Lambda
│   │   ├── submit_job/         # Lambda SubmitJob
│   │   ├── worker/             # Lambda Worker
│   │   ├── get_job_status/     # Lambda GetJobStatus
│   │   └── get_results/        # Lambda GetResults
│   ├── business_logic/         # Lógica de negocio
│   │   ├── toon_processor.py   # Procesamiento de toons
│   │   └── job_manager.py      # Gestión de jobs
│   └── utils/                  # Utilidades compartidas
│       ├── auth.py             # Validación JWT
│       ├── dynamodb.py         # Helpers DynamoDB
│       └── logger.py           # Logging estructurado
├── iac/                        # INFRAESTRUCTURA
│   ├── cloudformation-template.yaml  # Template principal
│   └── parameters.json         # Parámetros de despliegue
├── data/                       # DATOS DE PRUEBA
│   ├── sample_jobs.json        # Jobs de ejemplo
│   └── sample_toons.json       # Toons de ejemplo
└── requirements.txt            # Dependencias Python
```

## File Naming Conventions

- Archivos Python: snake_case.py
- Handlers Lambda: handler.py (dentro de cada carpeta de Lambda)
- Templates CloudFormation: kebab-case.yaml
- Datos de prueba: sample_*.json o test_*.csv
