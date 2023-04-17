# Proyecto Ingeniería de Datos: Mercado Electrico Español

El objetivo de este proyecto es recolectar los datos disponibilizados en el Sistema de Información del Operador del Sistema (Esios) pudiendo tener cuadros de mando, este proyecto se ha planteado como una ingesta en batch. Antes de explicar la arquitectura del proyecto, antes de empezar a explicar la Arquitectura del proyecto, vamos a explicar brevemente como funciona el Mercado Diario del Mercado Eléctrico Español.

## Mercado Eléctrico Diario

Nos estamos refiriendo desde luego al mercado mayorista eléctrico, que opera de forma diaria el operador de mercado eléctrico (OMIE, que sería como BME en el mercado financiero) y que suele conocerse como “pool” eléctrico.

Este término anglosajón de “pool” (que significa piscina en el idioma de Shakespeare) se deriva de la idea de que los vendedores y compradores mayoristas de energía eléctrica “arrojan” sus ofertas al mercado como si las lanzasen a una piscina.

Quienes arrojan las ofertas de venta son los generadores eléctricos (centrales nucleares, centrales de ciclo combinado, productores de energía con tecnología solar fotovoltaica, los propietarios de molinos que generan con energía eólica, etc..). Y quienes arrojan sus ofertas de compra son por lo general las compañías eléctricas, que luego actúan como comercializadores de los clientes finales (si bien algunos grandes consumidores industriales acuden directamente a comprar en el mercado).

Desde luego, como todo mercado, el objetivo final del “pool” es fijar un precio para cruzar la oferta y la demanda, cerrando así las transacciones de compraventa.

### ¿Qué significa marginalista?

Esencialmente significa que los productores han lanzado sus ofertas con diferentes precios, que podríamos ordenar de mayor a menor. Sin embargo, el precio que todos ellos recibirán por su energía será un mismo precio: el precio de mercado.

Que (y aquí viene el punto polémico) puede ser más alto que el precio al que estaban dispuestos a vender: aquél precio con el que habían ofertado.

Es decir, es el precio del margen, o precio marginal, el que se considera precio de mercado a cada hora del día.

De aquí derivan la mayor parte de críticas que se suelen realizar al mercado marginalista: el hecho de que algunos productores recibirán un precio por encima del precio al que podrían vender, y esto se puede entender injustificado o poco óptimo.

### Curva Agregada oferta y demanda

Con esta información se puede entender la "Curva Agregada Oferta y Demanda", donde se verán las diferentes ofertas de los generadores y demanda, llegando a un punto de interconexión que definará el Precio diario de la energía.

<div class="ai-center-all">
  <p align="center">
    <img width="800" src="https://elperiodicodelaenergia.com/wp-content/uploads/2018/11/Curva-agregada-de-demanda-y-oferta-1024x638.jpg?raw=true" alt="data stack">
  </p>
</div>

## Arquitectura del Proyecto
Como se ha mencionado inicialmente, se ha planteado el proyecto como una Ingesta en Batch, para facilitar la instalación de los diferentes servicios se ha hecho mediante contenedores de Docker, evitando conflictos en la instalación, además de esta forma se automatiza la instalación de una forma más sencilla, antes de explicar los productos utilizados, se ha querido compartir un esquema del proyecto a partir del cual podemos hacernos una idea del proceso llevado a cabo.

<div class="ai-center-all">
  <p align="center">
    <img width="800" src="https://github.com/JorgeZapataBD/spain_electricity_market_ingest/blob/main/images/ArquitecturaProyectoEsios.png?raw=true" alt="data stack">
  </p>
</div>

### Herramientas
Como se ha comentado, se han dockerizado todos los servicios utilizados, antes de adentrarnos en el funcionamiento del Pipeline completo vamos a proceder a explicar cada ua de las herramientas utilizadas.
- Apache Airflow: Apache Airflow es una plataforma de código abierto para desarrollar, programar y supervisar flujos de trabajo por lotes. El marco de trabajo extensible de Python de Airflow permite crear flujos de trabajo que se conectan con prácticamente cualquier tecnología. Una interfaz web ayuda a gestionar el estado de sus flujos de trabajo. 
- Apache Kafka: Apache Kafka es una plataforma distribuida para la transmisión de datos que permite no solo publicar, almacenar y procesar flujos de eventos de forma inmediata, sino también suscribirse a ellos. Está diseñada para administrar los flujos de datos de varias fuentes y enviarlos a distintos usuarios.
- MongoDB es un sistema de base de datos NoSQL, orientado a documentos y de código abierto. En lugar de guardar los datos en tablas, tal y como se hace en las bases de datos relacionales, MongoDB guarda estructuras de datos BSON (una especificación similar a JSON) con un esquema dinámico, haciendo que la integración de los datos en ciertas aplicaciones sea más fácil y rápida.
- Power BI es un servicio de análisis de datos de Microsoft orientado a proporcionar visualizaciones interactivas y capacidades de inteligencia empresarial con una interfaz lo suficientemente simple como para que los usuarios finales puedan crear por sí mismos sus propios informes y paneles.

## Despliegue del Proyecto
Una vez introducido todas las herramientas vamos a explicar como desplegar cada una ellas, además de abrir comunicación entre ellas, ya que al estar en "containers" de Docker diferentes. Toda la configuración de los documentos de despliegue se podrán encontrar en el directorio de Deployment, separado por herramientas.
### Apache Aiflow

Vamos a empezar con la instalación de Apache Airflow que será el Orquestador de tareas, que ejecutará operadores de Python que realizarán las operaciones de ETL del Pipeline, para el despliegue de la misma en Docker, se ha seguido la siguiente guía:

https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html

El único cambio realizado, es que se ha montado una imagen de apache-airflow personalizada, ya que no funcionaba correctamente la "feature" añadida el el docker-compose obtenido de la documentación. Una vez aplicado este cambio solo hay que seguir la guía compartida, hasta poder ver la interfaz de Apache Airflow como se ve a continuación.

<div class="ai-center-all">
  <p align="center">
    <img width="800" src="https://github.com/JorgeZapataBD/spain_electricity_market_ingest/blob/main/images/ApacheAirflowInit.png?raw=true" alt="data stack">
  </p>
</div>

### Apache Kafka & Zookeeper
Para Apache Kafka solo hay que utilizada las imágenes default como veremos en el Docker Compose, solo hay que tener en cuenta los LISTENERS aplicados en la configuración, ya que será los que necesitemos luego para poder conectar con los brokers desde los Operadores de Airflow.

     KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
     KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
     KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT

### MongoDB
Al igual que para Apache Kafka, este caso solo hay que desplegar la imagen correspondiente a Mongo DB, además, se ha añadido Mongo DB Express, que nos permite tener una interfaz para analizar los datos que nos lleguen a nuestra base de datos.

### Permitir Conexión entre Herramientas Dockerizadas
Como se ha mencionado, para poder conectar desde los operadores de Apache Airflow a Kafka y Docker, será necesario añadir a la misma "network" los diferentes contenedores, en la siguiente documentación hay un ejemplo práctico.

https://devpress.csdn.net/opensource/62f4f32fc6770329307fabb2.html

En este proyecto, por ejemplo, habría que añadir MongoDB a la red de airflow, para ello el comando es el siguiente (dependerá del nombre de configuración de vuestra red y el id de vuestro contenedor de MongoDB):

    docker network connect airflow_default c97fe02ca827

Una vez hecho esto ya se podrá inspeccionar la red para ver si se ha añadido dicho contenedor, además sacaremos el valor necesario para crear el conector a MongoDB desde apache airflow, ya que nos dará información de la IP a utilizar, esta información se puede sacar también inspeccionando el propio contenedor:

    docker network inspect 1745b0c51b75 

## Proceso ETL
Como se ha explicado, los datos son obtenidos de ESIOS, en nuestro caso nos centraremos en los indicadores, cada uno de estos contendrán información de diferentes parámtros del sistema eléctrico, como pueden ser, precio, generación, demanda.... Para profunidar en lo que nos ofrece este Sistema de Información, se añade la documentación en el apartado correspondiente.

Una vez explicado esto vamos a explicar en mayor profundidad el proceso de ETL realizado en este proyecto. Como ya se ha comentado, como orquestador de tareas se ha utilizado Apache Airflow, y en este caso, se han desarrollado en Python Operadores customizados, que nos permitarán llevar a cabo las operaciones deseadas siguiendo el orden establecido en el script del DAG (Directed Acyclic Graph), este el concepto central de Airflow, que agrupa tareas organizadas con dependencias y relaciones que indican cómo deben ejecutarse. Apache Airflow permite crear tareas dinámicas, esto nos permite crear un proceso totalmente escalable ya que nos permitirá añadir en cualquier momento nuevos indicadores, solo tendremos que añadirlo a la variable que contiene toda las variables necesarias para ejecutar el proyecto, en mi caso, he categorizado los indicadores en "tablas" en función de la información ofrecidada. Por lo tanto los recursos necesarios a crear en Apache Airflow son los siguientes:
- esios_project_init
- MongoDB connection
- HTTP connection to esios_api

Además como se habrá visto en la documentación de Docker de Apache Airflow, se montará un volumen de los directorios dags, plugins y logs, lo que nos permitirá operar sin necesidad de entrar a nuestros contenedores.

Una vez visto, el proceso es el mostrado en la Arquitectura, un primero proceso que conecta con ESIOS y envía los datos a Apache Kafka, este paso lo hacemos ya que nos permite utilizar estos eventos en "raw" por si los necesitasemos en cualquier otro servicio que no sea MongoDB, y posteriormente se lee de estos, y se envía a una colección del tipo "Time Serie" de MongoDB, previamente creada por el proceso de Airflow si no existía, quedando un esquema como el siguiente:

<div class="ai-center-all">
  <p align="center">
    <img width="800" src="https://github.com/JorgeZapataBD/spain_electricity_market_ingest/blob/main/images/ApacheAirflowDag.png?raw=true" alt="data stack">
  </p>
</div>

Como se puede ver, se crea una rama para cada indicador, y esto es totalmente dinámico, lo que nos permite añadir nuevos indicadores y tablas en cualquier momento, creando un dag para cada tabla y una rama para cada indicador dentro del DAG correspondiente. En la imagen se puede ver los diferentes pasos que se realizan, aún así vamos a explicar brevemente estos.
1. Crear colección de MongoDB si no existe, las colección serán del tipo TimeSeries, ya que para los datos que manejamos nos permitirá hacer consultas de forma más eficiente, en este caso nos basaremos en el nombre definido en las variables, y cada una de ellas agrupará diferentes indicares que representan un tipo de datos similar.
2. Se comprueba los últimos datos cargados a MongoDB, obteniendo la última fecha para que la siguiente ejecución a la API de Esios sea desde ese punto, en caso de no existir se traerá el histórico de un año de dicho indicador.

3. Se conecta con Esios y se envían los eventos a Apache Kafka, se hace una pequeña transformación para recoger en todos los eventos los metadatos del indicador, lo que nos permitirá poder utilizarlos en cualquier servicio que disponibilicemos los datos. En este caso utilizamos Kafka como herramienta intermedia, ya que nos permitiría disponibilizar los eventos en otro servicio si fuese necesario, ya que permite leer los eventos del mismo topic con diferentes grupos.

4. Se cargan los eventos en MongoDB tras leerlos en Kafka.

Además de estos pasos hay que tener en cuenta, que el DAG se ha configurado para que las ejecuciones sean manuales, pero se podría modificar para que por ejemplo se ejecutase cada hora si tuviesemos un servidor activo. Por otro lado Airflow nos permite todo tipo de control de las ejecuciones y dependencias de los diferentes operadores, por defecto, se configura para que solo se ejecute un operador si los anteriores han funcionado correctamente, pero en este caso, para la carga de Apache Kafka a MongoDB se ha configurado para que se ejecute una vez se hayan ejecutado todos los procesadores, aunque alguno haya terminado con errores, de esta forma aunque haya algún fallo en un indicador de Esios el resto se cargará correctamente, y como el último instante cargado se recupera por indicador no habrá problema en la siguiente ejecución.


## Cuadro de Mando

Una vez ingestados los eventos en MongoDB con una estructura que permite utilizarlos de forma cómoda, podemos conectar la BBDD a Power BI para poder sacar información de los datos, por ejemplo, en el siguiente Cuadro de Mando nos permite comparar el Precio Diario del Mercado Eléctrico en diferentes países de Europa.

<div class="ai-center-all">
  <p align="center">
    <img width="800" src="https://github.com/JorgeZapataBD/spain_electricity_market_ingest/blob/main/images/MercadoDiarioEuropa.png?raw=true" alt="data stack">
  </p>
</div>


## Documentacion

https://www.docker.com/

https://kafka.apache.org/

https://airflow.apache.org/

https://www.mongodb.com/

https://www.esios.ree.es/es

https://elperiodicodelaenergia.com/por-que-el-mercado-electrico-es-marginalista/

https://powerbi.microsoft.com/es-es/

