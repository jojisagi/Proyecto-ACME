@echo off
REM Script para probar el API Gateway con curl (Windows)

REM Configuracion
set API_ENDPOINT=https://YOUR-API-ID.execute-api.YOUR-REGION.amazonaws.com/prod
set USER_POOL_ID=YOUR-USER-POOL-ID
set CLIENT_ID=YOUR-CLIENT-ID

echo =========================================
echo Test Suite - Sistema de Votacion
echo =========================================
echo.

REM Test 1: Obtener resultados sin autenticacion
echo Test 1: GET /results (sin autenticacion)
curl -s -w "\nHTTP_CODE:%%{http_code}" "%API_ENDPOINT%/results"
echo.
echo.

REM Test 2: Intentar votar sin autenticacion
echo Test 2: POST /vote (sin autenticacion - debe fallar)
curl -s -w "\nHTTP_CODE:%%{http_code}" -X POST -H "Content-Type: application/json" -d "{\"gadgetId\": \"gadget-001\"}" "%API_ENDPOINT%/vote"
echo.
echo.

REM Test 3: Informacion para votar con autenticacion
echo Test 3: POST /vote (con autenticacion)
echo Para probar con autenticacion, necesitas:
echo 1. Crear un usuario en Cognito
echo 2. Obtener un token de autenticacion
echo.
echo Ejemplo de comando para autenticar:
echo aws cognito-idp initiate-auth ^
echo   --auth-flow USER_PASSWORD_AUTH ^
echo   --client-id %CLIENT_ID% ^
echo   --auth-parameters USERNAME=user@example.com,PASSWORD=YourPassword123!
echo.
echo Luego usar el IdToken en el header Authorization:
echo.
echo curl -X POST ^
echo   -H "Content-Type: application/json" ^
echo   -H "Authorization: Bearer $ID_TOKEN" ^
echo   -d "{\"gadgetId\": \"gadget-001\"}" ^
echo   "%API_ENDPOINT%/vote"
echo.
echo.

REM Test 4: Verificar CORS
echo Test 4: OPTIONS /vote (CORS preflight)
curl -s -w "\nHTTP_CODE:%%{http_code}" -X OPTIONS -H "Origin: http://localhost:3000" -H "Access-Control-Request-Method: POST" "%API_ENDPOINT%/vote"
echo.
echo.

echo =========================================
echo Tests completados
echo =========================================
echo.
echo NOTA: Edita este archivo y reemplaza:
echo   - YOUR-API-ID con tu API Gateway ID
echo   - YOUR-REGION con tu region AWS
echo   - YOUR-USER-POOL-ID con tu User Pool ID
echo   - YOUR-CLIENT-ID con tu Client ID
