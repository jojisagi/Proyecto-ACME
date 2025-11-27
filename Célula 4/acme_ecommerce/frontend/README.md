# E-commerce Frontend - React

Aplicación web React para el sistema de e-commerce serverless.

## Configuración

1. Instalar dependencias:
```bash
npm install
```

2. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con la URL de tu API Gateway
```

3. Ejecutar en desarrollo:
```bash
npm start
```

4. Construir para producción:
```bash
npm run build
```

5. Desplegar a S3:
```bash
aws s3 sync build/ s3://your-bucket-name --delete
```

## Características

- ✅ Lista de órdenes con paginación
- ✅ Crear nuevas órdenes
- ✅ Ver detalles de órdenes
- ✅ Estados visuales de órdenes
- ✅ Diseño responsive
- ✅ Integración con API Gateway

## Componentes

- `App.js` - Componente principal
- `OrderList.js` - Lista de órdenes
- `OrderForm.js` - Formulario de creación
- `OrderDetail.js` - Detalles de orden
- `api.js` - Cliente HTTP para API
