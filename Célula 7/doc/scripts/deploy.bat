@echo off
REM Script de despliegue completo del Sistema de Votacion (Windows)

echo =========================================
echo Despliegue Sistema de Votacion
echo =========================================
echo.

REM Variables
set REGION=us-east-1
set IAM_STACK_NAME=gadget-voting-iam
set MAIN_STACK_NAME=gadget-voting-main
set S3_BUCKET_NAME=gadget-voting-lambda-code-%RANDOM%

echo Paso 1: Crear bucket S3 para codigo Lambda
aws s3 mb s3://%S3_BUCKET_NAME% --region %REGION%
echo OK Bucket creado: %S3_BUCKET_NAME%
echo.

echo Paso 2: Empaquetar funciones Lambda
call package-lambdas.bat
echo.

echo Paso 3: Subir codigo Lambda a S3
aws s3 cp ..\dist\lambda\ s3://%S3_BUCKET_NAME%/lambda/ --recursive
echo OK Codigo Lambda subido
echo.

echo Paso 4: Desplegar stack IAM
aws cloudformation create-stack ^
  --stack-name %IAM_STACK_NAME% ^
  --template-body file://..\cloudformation\iam-stack.yaml ^
  --capabilities CAPABILITY_NAMED_IAM ^
  --region %REGION%

echo Esperando a que el stack IAM se complete...
aws cloudformation wait stack-create-complete ^
  --stack-name %IAM_STACK_NAME% ^
  --region %REGION%
echo OK Stack IAM desplegado
echo.

echo Paso 5: Desplegar stack principal
aws cloudformation create-stack ^
  --stack-name %MAIN_STACK_NAME% ^
  --template-body file://..\cloudformation\main-stack.yaml ^
  --parameters ^
    ParameterKey=IamStackName,ParameterValue=%IAM_STACK_NAME% ^
    ParameterKey=EmitVoteLambdaS3Bucket,ParameterValue=%S3_BUCKET_NAME% ^
  --region %REGION%

echo Esperando a que el stack principal se complete...
aws cloudformation wait stack-create-complete ^
  --stack-name %MAIN_STACK_NAME% ^
  --region %REGION%
echo OK Stack principal desplegado
echo.

echo Paso 6: Obtener outputs del stack
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %MAIN_STACK_NAME% --query "Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue" --output text --region %REGION%') do set API_ENDPOINT=%%i
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %MAIN_STACK_NAME% --query "Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue" --output text --region %REGION%') do set USER_POOL_ID=%%i
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %MAIN_STACK_NAME% --query "Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue" --output text --region %REGION%') do set CLIENT_ID=%%i

echo.
echo =========================================
echo Despliegue Completado
echo =========================================
echo.
echo API Endpoint: %API_ENDPOINT%
echo User Pool ID: %USER_POOL_ID%
echo Client ID: %CLIENT_ID%
echo.
echo Siguiente paso: Poblar datos de ejemplo
echo populate-data.bat
echo.
echo Configurar frontend:
echo cd ..\frontend
echo copy .env.example .env
echo REM Editar .env con los valores anteriores
echo npm install
echo npm start
