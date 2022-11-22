from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta  
from siteHelpers import *
from connectionString import *
import time

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = getWTFSecret()# Flask-WTF requires an encryption key - the string can be anything
Bootstrap(app)# Flask-Bootstrap requires this line
alchemyEngine = create_engine(getConnectionString(), pool_recycle=3600)
dbConnection = alchemyEngine.connect()

@app.route('/')
def home():
   sum=getCurrentValue(dbConnection)
   return render_template('home.html', value=sum)

@app.route('/tx')
def tx():
   df = pd.read_sql("select * from tx order by account, date_bought", dbConnection)
   df = pd.DataFrame(df, columns=      
   ['account','date_bought','shares','purchase_price','ticker',
   'current_price','current_value','gain_loss','last_update','purchase_value'])
   format_mapping={'account':'{}', 'date_bought':'{}', 'shares':'{}', 'purchase_price':'${:,.2f}' ,'ticker': '{}',
   'current_price':'${:,.2f}','current_value':'${:,.2f}','gain_loss':'${:,.2f}','last_update': '{}','purchase_value':'${:,.2f}'}
   for key, value in format_mapping.items():
     df[key] = df[key].apply(value.format)
   sum=getCurrentValue(dbConnection)
   return render_template('txTable.html',table_name = 'All Transactions', table = df.to_html(classes='data', header="true"),value=sum)
   
@app.route('/tx/<acct>')
def txAcct(acct):
   query = "select * from tx where account='"+acct+"' order by account, date_bought"
   df = pd.read_sql(text(query), dbConnection)
   df = pd.DataFrame(df, columns=      
   ['account','date_bought','shares','purchase_price','ticker',
   'current_price','current_value','gain_loss','last_update','purchase_value'])
   format_mapping={'account':'{}', 'date_bought':'{}', 'shares':'{}', 'purchase_price':'${:,.2f}' ,'ticker': '{}',
   'current_price':'${:,.2f}','current_value':'${:,.2f}','gain_loss':'${:,.2f}','last_update': '{}','purchase_value':'${:,.2f}'}
   for key, value in format_mapping.items():
     df[key] = df[key].apply(value.format)
   return '<header>All Transactions</header><br><a href="http://192.168.86.61:6969">Home</a><br>'+ df.to_html(classes='data', header="true")
   
@app.route('/history')
def history():
   start = time.time()
   query = "select * from history order by date"
   df = pd.read_sql(text(query), dbConnection)
   print("query: " + str(time.time() - start))
   queryTime = time.time()
   plt.figure(figsize=(20,10)) 
   fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3,figsize=(18,8))
   plt.subplots_adjust(left=0.05, bottom=0.07, right=.99, top=.95, wspace=.13, hspace=.25)
   ax1 = makeSubplot(df, ax1, "Total", "total_value", dbConnection)
   ax2 = makeSubplot(df, ax2, "Retirement", "retirement", dbConnection)
   ax3 = makeSubplot(df, ax3, "Brokerage", "brokerage", dbConnection)
   ax4 = makeSubplot(df, ax4, "IRA", "ira", dbConnection)
   ax5 = makeSubplot(df, ax5, "Crypto", "crypto", dbConnection)
   ax6 = makeSubplot(df, ax6, "Roth 401k", "roth_401k", dbConnection)
   print("plot time: " + str(time.time() - queryTime) )
   buf = BytesIO()
   fig.savefig(buf, format="png")
   data = base64.b64encode(buf.getbuffer()).decode("ascii")
   return f"<header><a href='http://192.168.86.61:6969'>home</a></header><br> <img src='data:image/png;base64,{data}'/align='left'>"
   
@app.route('/historyTable')
def historyTable():
   df = pd.read_sql("select * from history order by date", dbConnection)
   df = pd.DataFrame(df, columns=['date','total_value', 'roth_401k', 'trad_401k', 'crypto', 'retirement', 'brokerage', 'ira'])
   format_mapping={'date':'{}', 'total_value':'${:,.2f}', 'roth_401k':'${:,.2f}', 'trad_401k':'${:,.2f}', 'crypto':'${:,.2f}', 'retirement':'${:,.2f}', 'brokerage':'${:,.2f}', 'ira':'${:,.2f}'}
   for key, value in format_mapping.items():
     df[key] = df[key].apply(value.format)
   return '<header>All History</header><br><a href="http://192.168.86.61:6969">Home</a><br>'+ df.to_html(classes='data', header="true")

@app.route('/enter', methods=['GET', 'POST'])
def enter():
   form = TradeForm()
   if form.validate_on_submit():
      query = "insert into tx Values ('" +form.account.data + "', DATE '" + form.date.data + "', " + form.shares.data + ", " + form.price.data  + ", ' "+ form.ticker.data + "',0,0,0,DATE '2022-07-29',0)"
      with alchemyEngine.connect() as con:
         rs = con.execute(query) 
   return render_template('enter.html', form=form)

@app.route('/trackedTrades/Enter', methods=['GET', 'POST'])
def trackedEnter():
   form = TrackedTradeForm()
   if form.validate_on_submit():
      query = "insert into tracker Values (" + form.buyShares.data + ", " + form.buyPrice.data + ", '" + form.buyTicker.data  + "', "+ form.sellShares.data + ", " + form.sellPrice.data+ ", '"+ form.sellTicker.data + "', "+ "DATE'" +form.date.data + "')"
      print(query)
      with alchemyEngine.connect() as con:
         rs = con.execute(query) 
   return render_template('enter.html', form=form)

@app.route('/trackedTrades/Table')
def trackedTradesTable():
   updateTrackerPrices()
   df = pd.read_sql("select * from tracker order by date", dbConnection)
   df = pd.DataFrame(df, columns=['date','sellticker', 'sellshares', 'sellprice', 'buyticker', 'buyshares', 'buyprice','profit','profitpercent'])
   format_mapping={'date':'{}', 'sellticker':'{}', 'sellshares':'{:,.2f}', 'sellprice':'${:,.2f}', 'buyticker':'{}', 'buyshares':'{:,.2f}', 'buyprice':'${:,.2f}','profit':'${:,.2f}', 'profitpercent':'%{:,.2f}'}
   for key, value in format_mapping.items():
     df[key] = df[key].apply(value.format)
   profitdf = pd.read_sql("select sum(profit) from tracker", dbConnection)
   format = '{:,.2f}'
   profitdf['sum'] = profitdf['sum'].apply(format.format)
   totalProfit = profitdf.iloc[0]['sum']
   #return '<header>Tracked Trades</header><br><a href="http://192.168.86.61:6969">Home</a><br>'+ df.to_html(classes='data', header="true")
   return render_template('trackerTable.html',table_name = 'Tracked Trades', table = df.to_html(classes='data', header="true"),value=totalProfit)

if __name__ == '__main__':
   app.run('0.0.0.0',6969)
