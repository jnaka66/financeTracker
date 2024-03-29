import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import psycopg2
import yfinance as yf
from psycopg2connection import *
import time
import socket


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

def getGain(dbConnection):
    df = pd.read_sql("select ((sum(current_value)/sum(purchase_value)) *100)-100 as gain from tx", dbConnection)
    format = '%{:,.2f}'
    df['gain'] = df['gain'].apply(format.format)
    gain = df.iloc[0]['gain']
    return gain

def getAccountGain(account, dbConnection):
    df = pd.read_sql("select ((sum(current_value)/sum(purchase_value)) *100)-100 as gain from tx where account = '" + account+"'", dbConnection)
    format = '%{:,.2f}'
    df['gain'] = df['gain'].apply(format.format)
    gain = df.iloc[0]['gain']
    return gain

def makeSubplot(dfs, sp,title,account, dbConnection, colNames='' ):
    if(len(dfs) ==1):#regular /history page
        df = dfs[0]
        y = df[account].tolist()
        y = [value for value in y if value != 0] #filter 0s before data recorded this is not the slow part, e-5 time
        x = df.date.tolist()[-len(y):] #make dates same size as data
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
    else: #for /analysis page
        for i, df in enumerate(dfs):
            y = df[colNames[i]].tolist()
            #y = [value for value in y if value != 0] #filter 0s before data recorded this is not the slow part, e-5 time
            x = df.date.tolist()
            sp.plot(x, y)
        sp.set_title(title)
        sp.grid()
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

def updateTrackerPrices():
    conn = psycopg2.connect(user=getpsycopg2User(),
                                    password=getpsycopg2PW(),
                                    host=getpsycopg2Host(),
                                    port=getpsycopg2Port(),
                                    database=getpsycopg2db())
    cur = conn.cursor()

    #update sell side
    cur.execute("Select distinct sellticker from tracker;")
    distinctTickersTuple=cur.fetchall()
    distinctTickers=[]
    for ticker in distinctTickersTuple:
        distinctTickers.append(ticker[0].strip())
    prices = []
    for ticker in distinctTickers:
        curTicker = yf.Ticker(ticker)
        data = curTicker.history()
        last_quote = data['Close'].iloc[-1]
        prices.append(last_quote)
        cur.execute("UPDATE tracker SET sell_currentvalue = (%s) * sellshares where sellticker=(%s)",(last_quote,ticker))
    cur.execute("UPDATE tracker SET sellprofit = sell_currentvalue - (sellshares*sellprice)")
    
    #update buy side
    cur.execute("Select distinct buyticker from tracker;")
    distinctTickersTuple=cur.fetchall()
    distinctTickers=[]
    for ticker in distinctTickersTuple:
        distinctTickers.append(ticker[0].strip())
    prices = []
    for ticker in distinctTickers:
        curTicker = yf.Ticker(ticker)
        data = curTicker.history()
        last_quote = data['Close'].iloc[-1]
        prices.append(last_quote)
        cur.execute("UPDATE tracker SET buy_currentvalue = (%s) * buyshares where buyticker=(%s)",(last_quote,ticker))
    cur.execute("UPDATE tracker SET buyprofit = buy_currentvalue - (buyshares*buyprice)")
    #profit and profit%
    cur.execute("UPDATE tracker SET profit = (buyprofit - sellprofit)")
    cur.execute("UPDATE tracker SET profitpercent = (profit/(GREATEST(buyshares*buyprice,sellshares*sellprice)))*100")
    conn.commit()
    cur.close()
    conn.close()

def getWeights(arg,dbConnection): #I intend to expand options for this
    if(arg == 'agg vs lame'):
        #agg vs lame tickers is hardcoded, could use something like beta to determine, but this is for personal use
        lameTickers = ['VTI','VTSAX','cash','VOO','VFIAX','VFFSX']
        #get list of all tickers and eliminate the lames to get the aggs
        query = "select distinct ticker from tx"
        df = pd.read_sql(text(query), dbConnection)
        allTickers = df['ticker'].tolist()
        aggressiveTickers = [aggressiveTickers for aggressiveTickers in allTickers if aggressiveTickers not in lameTickers]
        #now get sums of holdings in each group to determine weights
        query = "select sum(current_value) from tx where ticker in ('" + "','".join(lameTickers) + "')"
        lamedf = pd.read_sql(text(query), dbConnection)
        query = "select sum(current_value) from tx where ticker in ('" + "','".join(aggressiveTickers) + "')"
        aggdf = pd.read_sql(text(query), dbConnection)
        lameSum = lamedf['sum'][0]
        aggSum = aggdf['sum'][0]
        lamePercent = round((lameSum / (lameSum+aggSum)) * 100,2) 
        aggPercent = round((aggSum / (lameSum+aggSum)) * 100,2)
        return aggPercent, lamePercent

def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


class TradeForm(FlaskForm):
    account = StringField('Account', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    shares = StringField('Shares', validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    ticker = StringField('Ticker', validators=[DataRequired()])
    submit = SubmitField('Submit')

class TrackedTradeForm(FlaskForm):
    date = StringField('Date', validators=[DataRequired()])
    buyShares = StringField('Buy Shares', validators=[DataRequired()])
    buyPrice = StringField('Buy Price', validators=[DataRequired()])
    buyTicker = StringField('Buy Ticker', validators=[DataRequired()])
    sellShares = StringField('Sell Shares', validators=[DataRequired()])
    sellPrice = StringField('Sell Price', validators=[DataRequired()])
    sellTicker = StringField('Sell Ticker', validators=[DataRequired()])
    submit = SubmitField('Submit')



