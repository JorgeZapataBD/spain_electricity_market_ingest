from airflow.models import BaseOperator,Variable
from airflow.providers.http.hooks.http import HttpHook
from airflow.providers.mongo.hooks.mongo import MongoHook
import json
from datetime import datetime,timedelta,timezone
from airflow_provider_kafka.hooks.producer import KafkaProducerHook
from airflow_provider_kafka.hooks.consumer import KafkaConsumerHook
import pandas as pd
import pytz


class EsiosApi2ApacheKafkaOperator(BaseOperator):
    """
    Rrealiza una petición al endpoint Esios API para obtener datos de cualquier indicador
    y envía el output a un topic de Apache Kafka
    :param http_conn_id: La referencia `http connection<howto/connection:http>` para realizar
                        la conexion con la api de esios
    :param endpoint: Ruta relativa de la url de conexion. En este caso se ha configurado
                     con el valor del indicador
    :param method: Metodo HTTP a usar, default = "POST"
    :param headers: Cabeceras HTTP headers a añadir a la peticion
    """
    ui_color = '#ededed'


    def __init__(
            self,
            endpoint,
            method,
            headers,
            kafka_config,
            kafka_topic,
            poll_timeout = 0,
            synchronous = True,
            http_conn_id = "http_default",
            *args,**kwargs
        ):
        super().__init__(*args,**kwargs)
        self.http_conn_id = http_conn_id
        self.method = method
        self.endpoint = endpoint
        self.kafka_topic = kafka_topic
        self.synchronous = synchronous
        self.poll_timeout = poll_timeout
        self.kafka_config = kafka_config or {}
        self.headers = headers or {}
      
    def execute(self,context):
        http = HttpHook(
            http_conn_id =  self.http_conn_id,
            method=self.method
        )
        # Get producer and callable
        producer = KafkaProducerHook(
            kafka_conn_id=None,
            config=self.kafka_config
        ).get_producer()

        # Obtener valor de la variable generada por GetDatetimeRangeMongoDB
        dates_range = Variable.get(f'dates_range_{self.endpoint}',
            default_var=[],
            deserialize_json=True)
        all_events = []

        #Se realizan el número de peticiones necesarias en funcion de la variable obtenida con el array de fechas
        for start, end in zip(dates_range[:-1], dates_range[1:]):
            end = (datetime.strptime(end, "%Y-%m-%dT%H:%M:%S%z") - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%S%z")
            response = http.run(self.endpoint, {"start_date": start, "end_date": end}, self.headers)
            print(response.url)
            result = json.loads(response.text)
            if len(result["indicator"]["values"])>0:
                for value in result["indicator"]["values"]:
                    event_dict = {
                        "metadata": {}
                    }
                    event_dict["metadata"].setdefault("id",result["indicator"]["id"])
                    event_dict["metadata"].setdefault("geo_id",value["geo_id"])
                    event_dict["metadata"].setdefault("geo_name",value["geo_name"])
                    event_dict["metadata"].setdefault("name",result["indicator"]["name"])
                    event_dict["metadata"].setdefault("step_type",result["indicator"]["step_type"])
                    event_dict["metadata"].setdefault("magnitude",result["indicator"]["magnitud"])
                    event_dict["metadata"].setdefault("period",result["indicator"]["tiempo"])
                    event_dict.setdefault("datetime",value["datetime"])
                    event_dict.setdefault("value",value["value"])
                    producer.produce(self.kafka_topic,value = json.dumps(event_dict))
                    producer.flush()
                print(f"Publish Events to Kafka topic {self.kafka_topic}: ", len(all_events))
            else:
                print(f"Not events from {self.endpoint} indicator in this period")
            
            
class ApacheKafkaOperator2MongoDB(BaseOperator):

    ui_color = '#ededed'

    """
    Read Data from Kafka and send to MongoDB Collection
    :param kafka_config: 
    :param kafka_config:
    :param mongo_conn_id: 
    :param mongo_db: 
    :param mongo_collection: 
    """
    def __init__(
            self,
            kafka_config,
            kafka_topic,
            mongo_conn_id,
            mongo_db,
            mongo_collection,
            max_batch_size: int = 1000,
            poll_timeout: int = 120,
            *args,**kwargs
        ):
        super().__init__(*args,**kwargs)
        self.kafka_topic = kafka_topic
        self.kafka_config = kafka_config or {}
        self.max_batch_size = max_batch_size
        self.poll_timeout = poll_timeout
        self.mongo_conn_id = mongo_conn_id
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection

    def execute(self, context):
        # Get producer and callable
        consumer = KafkaConsumerHook(
            topics=self.kafka_topic, 
            kafka_conn_id=None, 
            config=self.kafka_config
        ).get_consumer()

        

        while True:  # bool(True > 0) == True
            msgs = consumer.consume(num_messages=self.max_batch_size, timeout=self.poll_timeout)
            if not msgs:  # No messages
                self.log.info("Reached end of log. Exiting.")
                break     
            consumer.commit()
            msgs = [json.loads(msg.value()) for msg in msgs]
            for msg in msgs:
                msg['datetime'] = datetime.strptime(msg['datetime'], "%Y-%m-%dT%H:%M:%S.%f%z")
            hook = MongoHook(mongo_conn_id=self.mongo_conn_id)
            client = hook.get_conn()
            db = client[self.mongo_db]
            currency_collection=db[self.mongo_collection]
            print(f"Connected to MongoDB - {client.server_info()}")
            currency_collection.insert_many(msgs)
            print("Correct send message to mongodb: ", len(msgs))
        consumer.close()

        return True
    
class GetDatetimeRangeMongoDB(BaseOperator):

    ui_color = '#ededed'

    """
    Obtiene la última fecha cargada en una coleccion para cada uno de los indicadores en funcion
    de una query ejecutada.
    :param airflow_variable: Variable en el que se asignara el array de fechas 
    :param mongo_conn_id:  Id de la conexion de mongo generada en Airflow
    :param mongo_db: Base de datos
    :param mongo_collection: Coleccion
    :param mongo_timeseries: Configuracion de la Time Serie
    :param mongo_query: Filtro a ejecutar 
    :param mongo_projection: Funciones de agregacion como ordenar los eventos
    """
    def __init__(
            self,
            airflow_variable,
            mongo_conn_id,
            mongo_db,
            mongo_collection,
            mongo_query,
            mongo_projection,
            *args,**kwargs
        ):
        super().__init__(*args,**kwargs)
        self.airflow_variable = airflow_variable
        self.mongo_conn_id = mongo_conn_id
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.mongo_query = mongo_query
        self.mongo_projection = mongo_projection

    def execute(self, context):
        hook = MongoHook(mongo_conn_id=self.mongo_conn_id)
        client = hook.get_conn()
        mydb = client[self.mongo_db]
        mycol = mydb[self.mongo_collection]
        

        # Realizamos la query y comprobamos si existen eventos para ese indicador, si no es así recuperamos los eventos del año anterior
        result = mycol.find_one(self.mongo_query,sort=self.mongo_projection)
        if result:
            print("Actual Datetime Offset of indicator: ",result["datetime"].replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z"))
            start_dt = (result["datetime"] + timedelta(minutes=1)).replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
        else:
            print("Not Data from this Indicator, inital offset is one year ago")
            start_dt = (datetime.utcnow() - timedelta(days=365)).replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")

        end_dt = (datetime.utcnow() +
            timedelta(days=2)).replace(tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")   
         
        # Para evitar problemas de timeout en la API de Esios, tenemos que separar en periodos de 1 mes, y posteriormente se haran
        # tantas peticiones a la API de Esios como periodos se creen
        load_period = (datetime.strptime(end_dt, "%Y-%m-%dT%H:%M:%S%z") - datetime.strptime(start_dt, "%Y-%m-%dT%H:%M:%S%z")).days
        if load_period>30:
            dates_range = (pd.date_range(start_dt,end_dt , freq='M')-pd.offsets.MonthBegin(1)).tolist()
            
            dates_range = [value.strftime("%Y-%m-%dT00:00:00%z") for value in dates_range]
            dates_range.append(end_dt)
            dates_range[0] = start_dt
        else:
            dates_range = [start_dt,end_dt] 

        dates_range = [datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z").astimezone(tz=pytz.timezone('Europe/Madrid')).strftime("%Y-%m-%dT%H:%M:%S%z") for date in dates_range] 
        #Creamos la variable que será usada por el siguiente operador
        Variable.set(key=self.airflow_variable,
            value=dates_range, 
            serialize_json=True)
        return dates_range
       
class CreateTimeSerieCollection(BaseOperator):

    ui_color = '#ededed'

    """
    Crea TimeSerie Collection si no existe
    :param mongo_conn_id:  Id de la conexion de mongo generada en Airflow
    :param mongo_db: Base de datos
    :param mongo_collection: Coleccion
    :param mongo_timeseries: Configuracion de la Time Serie
    """
    def __init__(
            self,
            mongo_conn_id,
            mongo_db,
            mongo_collection,
            mongo_timeseries,
            *args,**kwargs
        ):
        super().__init__(*args,**kwargs)
        self.mongo_conn_id = mongo_conn_id
        self.mongo_db = mongo_db
        self.mongo_collection = mongo_collection
        self.mongo_timeseries = mongo_timeseries

    def execute(self, context):
        hook = MongoHook(mongo_conn_id=self.mongo_conn_id)
        client = hook.get_conn()
        db = client[self.mongo_db]
        if not self.mongo_collection in db.list_collection_names():
            db.create_collection(self.mongo_collection, timeseries=self.mongo_timeseries)
            print(f"Collection {self.mongo_collection} created correctly")
        else:
            print(f"Collection {self.mongo_collection} already exist")
        return True        
