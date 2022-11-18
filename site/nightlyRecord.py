import pandas as pd
from sqlalchemy import create_engine, text
import psycopg2 as pg
from datetime import date

alchemyEngine = create_engine('postgresql+psycopg2://jer:QASWEDFR1@127.0.0.1', pool_recycle=3600)
dbConnection = alchemyEngine.connect()
connection = alchemyEngine.raw_connection()
cursor = connection.cursor()

insertQuery = "insert into history Values ('" + date.today().strftime("%Y-%m-%d")+"', '"
df = pd.read_sql("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name   = 'history' ", dbConnection)
for index, row in df.iterrows():
    col = row['column_name']
    if col == 'date':#skip
        continue
    elif col == 'retirement': #special case
        answer = pd.read_sql("SELECT sum(current_value) FROM tx WHERE account in ('ira', 'roth_401k', 'trad_401k') ", dbConnection)
    elif col == 'total_value': #special case
        answer = pd.read_sql("SELECT sum(current_value) FROM tx", dbConnection)
    else:
        query = "select sum(current_value) from tx where account='"+col+"'"
        answer = pd.read_sql(text(query), dbConnection)
    if(index<df.size-1):
        insertQuery = insertQuery + str(answer['sum'][0]) + "', '"
    else:
        insertQuery = insertQuery + str(answer['sum'][0])
insertQuery = insertQuery + "')"
print(insertQuery)
cursor.execute(insertQuery)
connection.commit()
connection.close()


