import psycopg2
import streamlit as st

def get_connection(
    host: str = "localhost",
    port: int = 5432,
    dbname: str = "tonotron",
    user: str = "postgres",
    password: str = "aVs#1105"
):

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )

