@echo off
REM Script para limpiar todos los recursos AWS (Windows)

set MAIN_STACK_NAME=%1
set IAM_STACK_NAME=%2

if "%MAIN_STACK_NAME%"=="" set MAIN_STACK_NAME=gadget-voting-main
if "%IAM_STACK_NAME%"=="" set IAM_STACK_NAME=gadget-voting-iam

echo =========================================
echo Limpieza de Recursos AWS
echo =========================================
echo.
echo ADVERTENCIA: Esto eliminara todos los recursos creados
echo Stack Principal: %MAIN_STACK_NAME%
echo Stack IAM: %IAM_STACK_NAME%
echo.
set /p CONFIRM="Continuar? (y/n): "

if /i not "%CONFIRM%"=="y" (
    echo Operacion cancelada
    exit /b 1
)

REM Obtener bucket S3
echo Obteniendo informacion del bucket S3...
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name %MAIN_STACK_NAME% --query "Stacks[0].Parameters[?ParameterKey==`EmitVoteLambdaS3Bucket`].ParameterValue" --output text 2^>nul') do set S3_BUCKET=%%i

REM Eliminar stack principal
echo Eliminando stack principal...
aws cloudformation delete-stack --stack-name %MAIN_STACK_NAME%
echo Esperando a que se complete la eliminacion...
aws cloudformation wait stack-delete-complete --stack-name %MAIN_STACK_NAME%
echo OK Stack principal eliminado
echo.

REM Eliminar stack IAM
echo Eliminando stack IAM...
aws cloudformation delete-stack --stack-name %IAM_STACK_NAME%
echo Esperando a que se complete la eliminacion...
aws cloudformation wait stack-delete-complete --stack-name %IAM_STACK_NAME%
echo OK Stack IAM eliminado
echo.

REM Eliminar bucket S3
if not "%S3_BUCKET%"=="" (
    echo Eliminando bucket S3: %S3_BUCKET%...
    aws s3 rb s3://%S3_BUCKET% --force 2>nul
    echo OK Bucket S3 eliminado
)

echo.
echo =========================================
echo Limpieza completada
echo =========================================
echo.
echo Todos los recursos han sido eliminados.
echo.
echo Nota: Los logs de CloudWatch se mantienen por defecto.
echo Para eliminarlos manualmente:
echo   aws logs delete-log-group --log-group-name /aws/lambda/GadgetVoting-EmitVote
echo   aws logs delete-log-group --log-group-name /aws/lambda/GadgetVoting-GetResults
echo   aws logs delete-log-group --log-group-name /aws/lambda/GadgetVoting-StreamProcessor
