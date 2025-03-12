from datetime import datetime, timedelta
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook

# DAG 환경변수 설정
default_arg = {
    'owner': 'airflow',                 # DAG 소유자 지정
    'depends_on_past': False,           # 이전 실행의 성공 여부에 관계없이 실행
    'start_date': datetime(2023,1,1),   # DAG 시작 날짜
    'retries': 1,                       # 실패 시 재시도 횟수
    'retry_delay': timedelta(minutes=5) # 재시도 간격 (5분)
}

# DAG 객체 생성 : 이름은 'openapi_to_mysql', 매일 실행되도록 schedule_interval 지정
dag = DAG(
    'openapi_to_mysql', 
    default_args=default_arg, 
    schedule_interval='@daily',
    tags=['api', 'mysql']
    )


def fetch_cat_fact(**kwargs):
    """
    OpenAPI (JsonPlaceholder)에서 데이터를 가져오는 함수.
    HTTP GET 요청을 통해 데이터를 받아오고 JSON 형태로 파싱하여 반환한다.
    반환된 데이터는 XCom을 통해 다음 태스크로 전달
    """
    url = 'https://catfact.ninja/fact'
    response = requests.get(url)
    data = response.json()
    return data

def insert_cat_fact(**kwargs):
    """
    fetch_cat_fact 태스크로부터 전달받은 데이터를 MYSQL에 저장하는 함수
    MySQL 연결은 airflow Connection ID 'mysql_default'를 사용한다.
    테이블이 없으면 먼저 생성하고, 데이터를 삽입
    """
    ti = kwargs['ti']
    data = ti.xcom_pull(task_ids='fetch_cat_fact')

    # MySQL 연결 (Airflow Connection 설정에서 mysql_default로 등록되어 있어야 함)
    mysql_hook = MySqlHook(mysql_conn_id='mysql_default')

    # cat_facts 테이블 생성 (없으면 생성)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS cat_facts(
        id INT AUTO_INCREMENT PRIMARY KEY,
        fact TEXT,
        length INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """

    mysql_hook.run(create_table_sql)
    
    # 데이터 삽입 SQL
    insert_sql = """
    INSERT INTO cat_facts (fact, length)
    VALUES (%s, %s)
    """
    record = (data.get('fact'), data.get('length'))
    mysql_hook.run(insert_sql, parameters=record)

# 데이터를 가져오는 태스크
fetch_cat_fact_task = PythonOperator(
    task_id='fetch_cat_fact',
    python_callable=fetch_cat_fact,
    provide_context=True,
    dag=dag
)


# 데이터를 MySQL에 삽입하는 태스크
insert_cat_fact_task = PythonOperator(
    task_id = 'insert_cat_fact',
    python_callable=insert_cat_fact,
    provide_context=True,
    dag=dag
)

# 태스크 순서 정의: fetch_cat_fact_task가 실행된 후 insert_cat_fact_task 실행
fetch_cat_fact_task >> insert_cat_fact_task