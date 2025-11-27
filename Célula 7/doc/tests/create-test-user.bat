@echo off
REM Script para crear usuario de prueba en Cognito (Windows)

set USER_POOL_ID=%1
set EMAIL=%2
set PASSWORD=%3

if "%USER_POOL_ID%"=="" set USER_POOL_ID=YOUR_USER_POOL_ID
if "%EMAIL%"=="" set EMAIL=test@example.com
if "%PASSWORD%"=="" set PASSWORD=TestPassword123!

echo Creando usuario de prueba en Cognito...
echo User Pool ID: %USER_POOL_ID%
echo Email: %EMAIL%
echo.

REM Obtener Client ID
echo Paso 1: Obteniendo Client ID...
for /f "tokens=*" %%i in ('aws cognito-idp describe-user-pool-clients --user-pool-id %USER_POOL_ID% --max-results 1 --query "UserPoolClients[0].ClientId" --output text') do set CLIENT_ID=%%i
echo Client ID: %CLIENT_ID%
echo.

REM Registrar usuario
echo Paso 2: Registrando usuario...
aws cognito-idp sign-up ^
  --client-id %CLIENT_ID% ^
  --username %EMAIL% ^
  --password %PASSWORD% ^
  --user-attributes Name=email,Value=%EMAIL%

echo OK Usuario registrado
echo.

REM Confirmar usuario
echo Paso 3: Confirmando usuario (bypass verificacion email)...
aws cognito-idp admin-confirm-sign-up ^
  --user-pool-id %USER_POOL_ID% ^
  --username %EMAIL%

echo OK Usuario confirmado
echo.

REM Obtener token
echo Paso 4: Obteniendo token de autenticacion...
for /f "tokens=*" %%i in ('aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --client-id %CLIENT_ID% --auth-parameters USERNAME^=%EMAIL%,PASSWORD^=%PASSWORD% --query "AuthenticationResult.IdToken" --output text') do set ID_TOKEN=%%i

echo OK Token obtenido
echo.
echo =========================================
echo Usuario de prueba creado exitosamente
echo =========================================
echo.
echo Email: %EMAIL%
echo Password: %PASSWORD%
echo.
echo ID Token (usar en Authorization header):
echo %ID_TOKEN%
echo.
echo Para probar el API:
echo set ID_TOKEN=%ID_TOKEN%
echo.
echo curl -X POST ^
echo   -H "Content-Type: application/json" ^
echo   -H "Authorization: Bearer %ID_TOKEN%" ^
echo   -d "{\"gadgetId\": \"gadget-001\"}" ^
echo   "YOUR_API_ENDPOINT/vote"
