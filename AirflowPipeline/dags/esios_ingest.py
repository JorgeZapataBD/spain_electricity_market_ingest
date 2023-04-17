
from datetime import datetime,timedelta
from airflow import DAG
from airflow.utils.trigger_rule import TriggerRule
from airflow.utils.task_group import TaskGroup
from airflow.models import Variable
from EsiosProject import GetDatetimeRangeMongoDB,EsiosApi2ApacheKafkaOperator,ApacheKafkaOperator2MongoDB,CreateTimeSerieCollection                     


variables = Variable.get('esios_project_init',
    default_var={},
    deserialize_json=True)
headers = variables["esios_headers"]
tables = variables["tables"]
kafka_config = variables["kafka_config"]
kafka_config_consumer = variables["kafka_config_consumer"]
def error_callback(err):
    print(err)
    print(f"Error connecting to Kafka Broker {kafka_config['bootstrap.servers']}")
    raise(err)
kafka_config["error_cb"] = error_callback

def create_dag(name,ids):
    default_dag_args = {
        'start_date': datetime(2019, 1, 1),
        'catchup': False,
        # 'email': ['jzapata@opensistemas.com'],
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=1),
    }
    with DAG(name,  
            description='esios_api',
            default_args=default_dag_args,
            schedule=None) as dag:
  
        create_collections = CreateTimeSerieCollection(
            task_id=f'create_collection_{name}',
            mongo_conn_id = "mongo_default",
            mongo_db = "pool_electrical_market",
            mongo_collection = name,
            mongo_timeseries = {"timeField": "datetime", "metaField": "metadata", "granularity": "minutes"})
        
        # Creacion del grupo de tareas diviendo dinamicamente para obtener
        # un hilo por cada indicador solicitado
        with TaskGroup('ApiEsiosToKafka',
                        prefix_group_id=False,
                        ) as dynamic_tasks_group:
            for id in ids:

                get_datetime_range = GetDatetimeRangeMongoDB(            
                    task_id=f'get_datetime_range_{id}',
                    airflow_variable = f'dates_range_{id}',
                    mongo_conn_id = "mongo_default",
                    mongo_db = "pool_electrical_market",
                    mongo_collection = name,
                    mongo_query = {"metadata.id": int(id)},
                    mongo_projection = [('datetime', -1)]
                )

                esios2kafka = EsiosApi2ApacheKafkaOperator(
                    task_id=f'indicator_{id}_to_kafka',
                    http_conn_id = "esios_api",
                    method="GET",
                    endpoint=id,
                    kafka_config = kafka_config,
                    kafka_topic = name,
                    headers=headers
                    )
                # Dependencias del grupo de tareas
                get_datetime_range >> esios2kafka

        # Como es posible que funcione    
        kafka2mongo = ApacheKafkaOperator2MongoDB(
            task_id=f"load_{name}_mongodb",
            kafka_config = kafka_config_consumer,
            kafka_topic = [name,],
            mongo_conn_id = "mongo_default",
            mongo_db = "pool_electrical_market",
            mongo_collection=name,
            trigger_rule=TriggerRule.ALL_DONE
            )

    # Dependencias del dag    
    create_collections >> dynamic_tasks_group >> kafka2mongo

# Bucle para crear dags dinámicos en función de la variable de las tablas
for table in tables:
    dag = create_dag(
        table["name"],
        table["ids"])
    globals()['dag_' + table["name"]] = dag

del dag


