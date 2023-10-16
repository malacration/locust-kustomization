import os, json
from locust import HttpUser, task, between, events
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
from datetime import date, datetime
from uuid import uuid4
from contextlib import contextmanager, ContextDecorator
from time import time
from locust import User, task, constant, events
from operator import length_hint





@contextmanager
def _manual_report(name):
    start_time = time()
    try:
        yield
    except Exception as e:
        events.request.fire(
            request_type="manual",
            name=name,
            response_time=(time() - start_time) * 1000,
            response_length=0,
            exception=e,
        )
        raise
    else:
        events.request.fire(
            request_type="manual",
            name=name,
            response_time=(time() - start_time) * 1000,
            response_length=0,
            exception=None,
        )


def manual_report(name_or_func):
    if callable(name_or_func):
        # used as decorator without name argument specified
        return _manual_report(name_or_func.__name__)(name_or_func)
    else:
        return _manual_report(name_or_func)


class MinioTest(User):
    wait_time = between(1, 2)
    
    minio_client = None

    bucket_name = "dev-minio-teste"
        
    @task(7)
    @manual_report
    def upload(self):
        arquivo = self.criar_arquivo()
        file_data = open(str(arquivo), 'rb')
        file_stat = os.stat(str(arquivo))
        self.minio_client.put_object(self.bucket_name, str(arquivo), file_data, length=file_stat.st_size, content_type="text/plain")

    @task(100)
    @manual_report
    def get_file(self):
        self.minio_client.get_object(self.bucket_name, "windson")


    @task(15)
    @manual_report
    def search_file(self):
        objs = self.minio_client.list_objects(
                self.bucket_name, recursive=True
            )
        print(length_hint(objs))
        for obj in objs:
            # print(obj.bucket_name, obj.object_name.encode('utf-8'), 
            #       obj.last_modified,
            #       obj.etag, obj.size, obj.content_type)
            self.minio_client.fget_object(
                obj.bucket_name,
                obj.object_name.encode("utf-8"),
                "/tmp/download"+obj.object_name.split("/")[-1]
            )
        

    def on_start(self):
        load_dotenv()
        print("Inicializando MinIO")
        minio_url = os.getenv("MINIO_URL")
        minio_access_key = os.getenv("ACCESS_KEY")
        minio_secret_key = os.getenv("SECRET_KEY")
        try:
            self.minio_client = Minio(
                minio_url,
                access_key=minio_access_key,
                secret_key=minio_secret_key,
                secure=True,
            )
            print("Cliente inicializado com sucesso.")
        except Exception as e:
            raise ValueError(f"[ERRO] Inicialização MinIO: {e.__str__()}")


    def criar_arquivo(self):
        unique=uuid4()
        arquivo=f"/tmp/teste-minio-{unique}.txt"
        escrever=f"teste-minio-{unique}"
        f = open(arquivo, "w")
        f.write(f"{escrever}\n")
        return arquivo