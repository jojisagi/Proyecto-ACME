# Guía de Contribución

Gracias por tu interés en contribuir al Sistema de Votación Gadget del Año.

## Cómo Contribuir

### Reportar Bugs

Si encuentras un bug, por favor crea un issue con:
- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Logs relevantes
- Versión de AWS CLI, Node.js, Python

### Sugerir Mejoras

Para sugerir nuevas características:
1. Verifica que no exista un issue similar
2. Describe el caso de uso
3. Explica el beneficio esperado
4. Propón una implementación si es posible

### Pull Requests

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código

#### Python (Lambda)
- Seguir PEP 8
- Docstrings para funciones
- Manejo de errores apropiado
- Logging para debugging

#### JavaScript/React
- ESLint con configuración estándar
- Componentes funcionales con hooks
- PropTypes o TypeScript
- CSS modular

#### CloudFormation
- YAML format
- Nombres descriptivos de recursos
- Outputs para valores importantes
- Comentarios para lógica compleja

### Testing

Antes de enviar un PR:
1. Probar localmente
2. Verificar que los scripts funcionen
3. Validar plantillas CloudFormation
4. Probar en cuenta AWS de desarrollo

### Documentación

- Actualizar README.md si es necesario
- Documentar nuevas variables de entorno
- Actualizar ARCHITECTURE.md para cambios arquitectónicos
- Incluir ejemplos de uso

## Código de Conducta

- Ser respetuoso y profesional
- Aceptar críticas constructivas
- Enfocarse en lo mejor para el proyecto
- Mostrar empatía hacia otros contribuidores

## Preguntas

Si tienes preguntas, abre un issue con la etiqueta "question".

## Licencia

Al contribuir, aceptas que tus contribuciones se licencien bajo la licencia MIT del proyecto.
