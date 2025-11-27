@echo off
REM Script para empaquetar funciones Lambda en Windows

echo Empaquetando funciones Lambda...

REM Crear directorio para los paquetes
if not exist "..\dist\lambda" mkdir "..\dist\lambda"

REM Empaquetar emit-vote
echo Empaquetando emit-vote...
cd ..\lambda\emit-vote
if exist temp rmdir /s /q temp
mkdir temp
copy lambda_function.py temp\
if exist requirements.txt (
    pip install -r requirements.txt -t temp\ --quiet
)
cd temp
powershell Compress-Archive -Path * -DestinationPath ..\..\..dist\lambda\emit-vote.zip -Force
cd ..
rmdir /s /q temp
cd ..\..\scripts
echo OK emit-vote.zip creado

REM Empaquetar get-results
echo Empaquetando get-results...
cd ..\lambda\get-results
if exist temp rmdir /s /q temp
mkdir temp
copy lambda_function.py temp\
if exist requirements.txt (
    pip install -r requirements.txt -t temp\ --quiet
)
cd temp
powershell Compress-Archive -Path * -DestinationPath ..\..\..dist\lambda\get-results.zip -Force
cd ..
rmdir /s /q temp
cd ..\..\scripts
echo OK get-results.zip creado

REM Empaquetar stream-processor
echo Empaquetando stream-processor...
cd ..\lambda\stream-processor
if exist temp rmdir /s /q temp
mkdir temp
copy lambda_function.py temp\
if exist requirements.txt (
    pip install -r requirements.txt -t temp\ --quiet
)
cd temp
powershell Compress-Archive -Path * -DestinationPath ..\..\..dist\lambda\stream-processor.zip -Force
cd ..
rmdir /s /q temp
cd ..\..\scripts
echo OK stream-processor.zip creado

echo.
echo Todas las Lambdas empaquetadas en dist\lambda\
echo.
echo Siguiente paso: Subir los archivos ZIP a S3
echo aws s3 cp dist\lambda\ s3://YOUR-BUCKET/lambda/ --recursive
