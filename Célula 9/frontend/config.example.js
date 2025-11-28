// Archivo de configuración de ejemplo
// Copiar a config.js y completar con valores reales después del despliegue

const CONFIG = {
    // URL del API Gateway (obtener de CloudFormation Outputs)
    apiEndpoint: 'https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com',
    
    // ID del User Pool de Cognito (obtener de CloudFormation Outputs)
    userPoolId: 'us-east-1_XXXXXXXXX',
    
    // ID del Client de Cognito (obtener de CloudFormation Outputs)
    clientId: 'xxxxxxxxxxxxxxxxxxxxxxxxxx',
    
    // Región de AWS
    region: 'us-east-1',
    
    // Nombre de la aplicación
    appName: 'Célula 9 - Vehicle Gadgets',
    
    // Versión
    version: '1.0.0'
};

// Exportar configuración
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
