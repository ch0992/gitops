from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# 기본 인자 설정
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

# DAG 객체 생성: 이름은 'test_dag', 매일 실행
dag = DAG(
    'test_dag',
    default_args=default_args,
    schedule_interval='@daily'
)

def hello_world():
    print("Hello World from test DAG!")

# PythonOperator를 사용한 태스크 정의
hello_task = PythonOperator(
    task_id='hello_task',
    python_callable=hello_world,
)