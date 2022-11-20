from flask import Flask, render_template
import psycopg2
import pandas as pd
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from siteHelpers import getCurrentValue, makeSubplot

app = Flask(__name__, template_folder='templates')
alchemyEngine = create_engine('postgresql+psycopg2://jer:QASWEDFR1@127.0.0.1', pool_recycle=3600)
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
   sum=getCurrentValue()
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
   plt.figure(figsize=(20,10)) 
   fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3,figsize=(18,8))
   plt.subplots_adjust(left=0.05, bottom=0.07, right=.99, top=.95, wspace=.13, hspace=.25)
   ax1 = makeSubplot(ax1, "Total", "total_value", dbConnection)
   ax2 = makeSubplot(ax2, "Retirement", "retirement", dbConnection)
   ax3 = makeSubplot(ax3, "Brokerage", "brokerage", dbConnection)
   ax4 = makeSubplot(ax4, "IRA", "ira", dbConnection)
   ax5 = makeSubplot(ax5, "Crypto", "crypto", dbConnection)
   ax6 = makeSubplot(ax6, "Roth 401k", "roth_401k", dbConnection)
   buf = BytesIO()
   fig.savefig(buf, format="png")
   data = base64.b64encode(buf.getbuffer()).decode("ascii")
   return f"<header><a href='http://192.168.86.61:6969'>home</a></header><br> <img src='data:image/png;base64,{data}'/align='left'>"
   
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
