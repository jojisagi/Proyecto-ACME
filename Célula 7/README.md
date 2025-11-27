#Cédula 7
Katia Marcela Carpio Domínguez
Alondra Hernández Martinez



#Cómo desplegar con el pipeline (GitHub → CodePipeline → CodeBuild → CloudFormation → sandbox / pre-prod / prod).



#Cómo probar con curl
Las pruebas están pensadas para ser realizadas en powershell y ser pegados tal cual en la línea de comandos. El detalle para probar están en la carpeta Cédula 7/data


##Pruebas Gadgets-locales
En el archivo en la carpeta Cédula 7/data/gadgetprueba-comando-powershell.txt se encuentra el comando que se debe usar para poder realizar la respectiva prueba.
Se copia tal cual el comando completo y se pega en la línea de comando de powershell. Se espera la siguiente respuesta: 

Gadget g1 insertado correctamente Respuesta: "Gadget g1 insertado correctamente"


##Pruebas votando
En el archivo en la carpeta Cédula 7/data/votar-comando-powershell.txt se encuentra el comando que se debe usar para poder realizar la respectiva prueba.
Se copia tal cual el comando completo después de la línea que indica las 50 pruebas juntas y se pega en la línea de comando de powershell.

Se esperan las siguientes respuestas según aplique: 

Error al insertar voto v1 por user1 para g10: {"message": "User has already voted"}

Error al insertar voto v1 por user999 para g999: {"message": "Gadget not found"}

Voto v1 por user1 para g1 para gadget g1 insertado correctamente

##Pruebas visualizando resultados votos

Se espera la siguiente respuesta: 

votes

{@{gadgetId=g7; totalVotes=4.0}, @{gadgetId=g6; totalVotes=5.0}, @{gadgetId=g2; totalVotes=8.0}, @{gadgetId=g10; tot...



#Qué hace cada Lambda y cada endpoint de la API.
##Lambdas
-emitvote-
Función Lambda que gestiona votos para gadgets utilizando varias tablas de DynamoDB. Primero recibe los datos del voto (usuario, voto y gadget) desde el cuerpo del evento, y verifica que el gadget exista en la tabla GadgetPrueba; si no existe, devuelve un error. Luego intenta registrar el voto en la tabla Votes, usando una condición que impide que un mismo usuario vote más de una vez. Si el usuario ya votó, se devuelve un mensaje de advertencia. Si el voto es válido, la función actualiza la tabla VoteResults incrementando el contador de votos para ese gadget, creando el registro si aún no existe. Finalmente, responde con un mensaje indicando que el voto se registró correctamente.

-voteresult-
Función Lambda en Python que se conecta a DynamoDB para obtener todos los registros almacenados en la tabla VoteResults. Primero realiza un scan para recuperar todos los ítems; si la tabla está vacía, responde con un mensaje indicando que aún no hay votos. Si sí existen resultados, convierte cualquier valor de tipo Decimal a float (ya que json.dumps no puede serializar Decimals) y finalmente devuelve un JSON con la lista completa de votos encontrados.

-gadgetprueba-
Función Lambda que recibe los datos de un gadget desde el evento HTTP (ya sea dentro de body como JSON o directamente en el evento) y los usa para insertar un nuevo registro en la tabla GadgetPrueba de DynamoDB. La función verifica que los campos obligatorios (gadgetId, nombre, categorias y descripcion) estén presentes; si falta alguno, responde con un error 400.

##Endpoints
/vote
El endpoint /vote recibe una solicitud para registrar un voto asociado a un gadget. Valida primero que el gadget exista en la base de datos y luego intenta guardar el voto en la tabla correspondiente, asegurándose de que un mismo usuario no pueda votar más de una vez. Si el registro es exitoso, incrementa el contador de votos del gadget en la tabla de resultados y devuelve un mensaje confirmando el voto

/voteResult
El endpoint /voteResult obtiene y devuelve el resumen de los votos registrados en la tabla de resultados. Realiza un escaneo completo de la tabla y, si no existen votos, informa que todavía no se ha realizado ninguno. En caso contrario, transforma los valores numéricos para poder enviarlos como JSON y devuelve una lista con el total de votos por gadget.

/gadgetprueba
El endpoint /gadgetprueba permite agregar nuevos gadgets a la tabla GadgetPrueba en DynamoDB. Recibe datos como el identificador del gadget, su nombre, sus categorías y su descripción. Valida que todos los parámetros estén presentes y luego inserta el registro en la base de datos. Si la operación se ejecuta correctamente, confirma la creación del gadget; si hay un error, devuelve un mensaje explicando el fallo.
