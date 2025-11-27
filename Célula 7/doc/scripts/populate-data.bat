@echo off
REM Script para poblar datos de ejemplo en DynamoDB (Windows)

echo Poblando datos de ejemplo en DynamoDB...

REM Verificar que AWS CLI este instalado
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: AWS CLI no esta instalado
    exit /b 1
)

echo Inicializando tabla VoteResults con gadgets...

REM Inicializar gadgets
aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-001\"}, \"gadgetName\": {\"S\": \"SmartWatch Pro X\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-001

aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-002\"}, \"gadgetName\": {\"S\": \"AirPods Ultra\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-002

aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-003\"}, \"gadgetName\": {\"S\": \"Drone Phantom 5\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-003

aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-004\"}, \"gadgetName\": {\"S\": \"VR Headset Elite\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-004

aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-005\"}, \"gadgetName\": {\"S\": \"Robot Aspiradora AI\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-005

aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-006\"}, \"gadgetName\": {\"S\": \"Tablet Creator Pro\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-006

aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-007\"}, \"gadgetName\": {\"S\": \"Smart Speaker Max\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-007

aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-008\"}, \"gadgetName\": {\"S\": \"Gaming Console Next\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-008

aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-009\"}, \"gadgetName\": {\"S\": \"E-Reader Premium\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-009

aws dynamodb put-item --table-name VoteResults --item "{\"gadgetId\": {\"S\": \"gadget-010\"}, \"gadgetName\": {\"S\": \"Smart Thermostat\"}, \"totalVotes\": {\"N\": \"0\"}}" --no-cli-pager
echo OK gadget-010

echo.
echo Insertando votos de ejemplo desde sample-votes.json...
echo Nota: Este proceso puede tardar unos minutos...

REM Usar Python para procesar el JSON e insertar votos
python -c "import json, subprocess, uuid, datetime; votes = json.load(open('../data/sample-votes.json')); [subprocess.run(['aws', 'dynamodb', 'put-item', '--table-name', 'Votes', '--item', json.dumps({'userId': {'S': v['userId']}, 'voteId': {'S': 'VOTE'}, 'gadgetId': {'S': v['gadgetId']}, 'timestamp': {'S': datetime.datetime.utcnow().isoformat()}, 'voteUuid': {'S': str(uuid.uuid4())}}), '--no-cli-pager'], capture_output=True) for v in votes]; print(f'OK {len(votes)} votos insertados')"

echo.
echo OK Datos poblados exitosamente
echo   - 10 gadgets inicializados en VoteResults
echo   - 50 votos insertados en Votes
echo.
echo Nota: Los votos se agregaran automaticamente a VoteResults
echo       mediante el StreamProcessor Lambda en unos segundos.
