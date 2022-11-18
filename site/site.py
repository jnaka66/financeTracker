from flask import Flask, render_template
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from siteHelpers import getCurrentValue

app = Flask(__name__, template_folder='templates')
alchemyEngine = create_engine('postgresql+psycopg2://jer:QASWEDFR1@127.0.0.1', pool_recycle=3600)
dbConnection = alchemyEngine.connect()

@app.route('/')
def home():
   sum=getCurrentValue()
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
   sum=getCurrentValue()
   return render_template('txTable.html',table_name = 'All Transactions', table = df.to_html(classes='data', header="true"),value=sum)
   #return '<header>All Transactions</header><br><a href="http://192.168.86.61:6969">Home</a><br>'+ df.to_html(classes='data', header="true")
   
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
   df = pd.read_sql("select * from history order by date", dbConnection)
   x_axis = df.date.tolist()
   y_axis = df.total_value.tolist()
   fig = plt.figure(figsize=(15, 10), dpi=80)
   ax = fig.subplots()
   ax.plot(x_axis, y_axis)
   ax.grid()
   fmt_month = mdates.MonthLocator()
   fmt_year = mdates.YearLocator()
   ax.xaxis.set_minor_locator(fmt_month)
   ax.xaxis.set_minor_formatter(mdates.DateFormatter('%b'))
   ax.xaxis.set_major_locator(fmt_year)
   ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
   ax.tick_params(labelsize=20, which='both')
   # create a second x-axis beneath the first x-axis to show the year in YYYY format
   sec_xaxis = ax.secondary_xaxis(-0.1)
   sec_xaxis.xaxis.set_major_locator(fmt_year)
   sec_xaxis.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
   buf = BytesIO()
   fig.savefig(buf, format="png")
   data = base64.b64encode(buf.getbuffer()).decode("ascii")
   return f"<a href='http://192.168.86.61:6969'>home</a> <img src='data:image/png;base64,{data}'/>"
   
@app.route('/historyTable')
def historyTable():
   df = pd.read_sql("select * from history order by date", dbConnection)
   df = pd.DataFrame(df, columns=['date','total_value'])
   format_mapping={'date':'{}', 'total_value':'${:,.2f}'}
   for key, value in format_mapping.items():
     df[key] = df[key].apply(value.format)
   return '<header>All History</header><br><a href="http://192.168.86.61:6969">Home</a><br>'+ df.to_html(classes='data', header="true")

if __name__ == '__main__':
   app.run('0.0.0.0',6969)
