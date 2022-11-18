import pandas as pd
from sqlalchemy import create_engine


def getCurrentValue():
    alchemyEngine = create_engine('postgresql+psycopg2://jer:QASWEDFR1@127.0.0.1', pool_recycle=3600)
    dbConnection = alchemyEngine.connect()
    df = pd.read_sql("select sum(current_value) from tx", dbConnection)
    format = '{:,.2f}'
    df['sum'] = df['sum'].apply(format.format)
    sum = df.iloc[0]['sum']
    return sum
