from datetime import datetime, timedelta
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook

# DAG 환경변수 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 객체 생성
dag = DAG(
    'mysql_exception',
    default_args=default_args,
    schedule_interval='@daily',
    tags=['api','mysql']
    )

# MySQL 연결 ID 설정
MYSQL_CONN_ID = "mysql_default"

def fetch_cat_fact(**kwargs):
    """
    OpenAPI (catfact.ninja)에서 데이터를 가져오는 함수.
    HTTP GET 요청을 통해 데이터를 받아오고 JSON 형태로 파싱하여 반환한다.
    반환된 데이터는 XCom을 통해 다음 태스크로 전달
    """
    url = 'https://catfact.ninja/fact'
    try:
        response = requests.get(url, timeout=10)  # 10초 타임아웃 설정
        response.raise_for_status()  # HTTP 오류 발생 시 예외 처리
        data = response.json()

        if not data or 'fact' not in data or 'length' not in data:
            raise ValueError("API에서 예상한 데이터를 받지 못했습니다.")

        return data  # XCom을 통해 다음 태스크로 전달
    except Exception as e:
        raise RuntimeError(f"API 요청 실패: {e}")

def insert_cat_fact(**kwargs):
    """
    fetch_cat_fact 태스크로부터 전달받은 데이터를 MySQL에 저장하는 함수
    MySQL 연결은 airflow Connection ID 'mysql_default'를 사용한다.
    테이블이 없으면 먼저 생성하고, 데이터를 삽입
    """
    ti = kwargs['ti']
    data = ti.xcom_pull(task_ids='fetch_cat_fact')

    if not data:
        raise ValueError("fetch_cat_fact에서 데이터가 전달되지 않았습니다.")

    fact_text = data.get('fact')
    fact_length = data.get('length')

    if not fact_text or fact_length is None:
        raise ValueError("MySQL에 저장할 데이터가 올바르지 않습니다.")

    try:
        # MySQL 연결 (Airflow Connection 설정에서 mysql_default로 등록되어 있어야 함)
        mysql_hook = MySqlHook(mysql_conn_id=MYSQL_CONN_ID)

        # cat_facts 테이블 생성 (없으면 생성)
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS cat_facts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fact TEXT NOT NULL,
            length INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        mysql_hook.run(create_table_sql)
        
        # 데이터 삽입 SQL
        insert_sql = """
        INSERT INTO cat_facts (fact, length)
        VALUES (%s, %s)
        """
        mysql_hook.run(insert_sql, parameters=(fact_text, fact_length))

    except Exception as e:
        raise RuntimeError(f"MySQL 데이터 삽입 실패: {e}")

# 데이터를 가져오는 태스크
fetch_cat_fact_task = PythonOperator(
    task_id='fetch_cat_fact',
    python_callable=fetch_cat_fact,
    dag=dag
)

# 데이터를 MySQL에 삽입하는 태스크
insert_cat_fact_task = PythonOperator(
    task_id='insert_cat_fact',
    python_callable=insert_cat_fact,
    dag=dag
)

# 태스크 순서 정의: fetch_cat_fact_task 실행 후 insert_cat_fact_task 실행
fetch_cat_fact_task >> insert_cat_fact_task