# Dashboard de Votación - Gadget del Año

Dashboard en tiempo real para el sistema de votación construido con React.

## Configuración

1. Instalar dependencias:
```bash
npm install
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
```

Editar `.env` con los valores de tu stack AWS:
- `REACT_APP_API_ENDPOINT`: URL del API Gateway
- `REACT_APP_USER_POOL_ID`: ID del User Pool de Cognito
- `REACT_APP_CLIENT_ID`: ID del Client de Cognito

3. Iniciar en modo desarrollo:
```bash
npm start
```

4. Construir para producción:
```bash
npm run build
```

## Características

- Autenticación con AWS Cognito
- Votación en tiempo real
- Dashboard con resultados actualizados cada 3 segundos
- Gráficos interactivos con Recharts
- Diseño responsive
- Validación de voto único por usuario

## Estructura

```
src/
├── components/
│   ├── Login.js              # Componente de autenticación
│   ├── VotingDashboard.js    # Dashboard principal
│   └── ResultsChart.js       # Gráfico de resultados
├── services/
│   ├── auth.js               # Servicio de autenticación Cognito
│   └── api.js                # Cliente API Gateway
├── App.js                    # Componente principal
└── index.js                  # Punto de entrada
```

## Despliegue

Para desplegar en S3 + CloudFront:

1. Construir la aplicación:
```bash
npm run build
```

2. Subir a S3:
```bash
aws s3 sync build/ s3://your-bucket-name --delete
```

3. Invalidar caché de CloudFront (si aplica):
```bash
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```
