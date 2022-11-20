import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure


def getCurrentValue(dbConnection):
    df = pd.read_sql("select sum(current_value) from tx", dbConnection)
    format = '{:,.2f}'
    df['sum'] = df['sum'].apply(format.format)
    sum = df.iloc[0]['sum']
    return sum

def getAccountLastValue(account, dbConnection):
    query = "select " + account + " from history order by date desc limit 1"
    df = pd.read_sql(text(query), dbConnection)
    format = '{:,.2f}'
    df[account] = df[account].apply(format.format)
    value = df.iloc[0][account]
    return value

def makeSubplot(sp,title,account, dbConnection):
    query = "select date, " + account + " from history where " + account + " is not null order by date"
    df = pd.read_sql(text(query), dbConnection)
    y = df[account].tolist()
    x = df.date.tolist()
    sp.plot(x, y)
    sp.grid()
    sp.set_title(title + ": $" + getAccountLastValue(account,dbConnection))
    fmt_month = mdates.MonthLocator()
    fmt_year = mdates.YearLocator()
    sp.xaxis.set_minor_locator(fmt_month)
    sp.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
    sp.xaxis.set_major_locator(fmt_year)
    sp.xaxis.set_major_formatter(mdates.DateFormatter('%b')) 
    sp.tick_params(labelsize=10, which='both')
    # create a second x-axis beneath the first x-axis to show the year in YYYY format
    sec_xaxis = sp.secondary_xaxis(-0.1)
    sec_xaxis.xaxis.set_major_locator(fmt_year)
    sec_xaxis.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    return sp

