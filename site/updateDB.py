import yfinance as yf
import psycopg2
from datetime import date
from psycopg2connection import *

def update_DB():
    print("test")
    conn = psycopg2.connect(user=getpsycopg2User(),
                                    password=getpsycopg2PW(),
                                    host=getpsycopg2Host(),
                                    port=getpsycopg2Port(),
                                    database=getpsycopg2db())
    cur = conn.cursor()
    cur.execute("Select distinct ticker from tx;")
    distinctTickersTuple=cur.fetchall()
    distinctTickers=[]
    for ticker in distinctTickersTuple:
        distinctTickers.append(ticker[0].strip())
    distinctTickers.remove("cash")
    print(distinctTickers)
    prices = []
    for ticker in distinctTickers:
        curTicker = yf.Ticker(ticker)
        data = curTicker.history()
        last_quote = data['Close'].iloc[-1]
        prices.append(last_quote)
        print(ticker, last_quote)
        cur.execute("UPDATE tx SET current_price = (%s), current_value = shares*(%s), last_update = (%s) where ticker=(%s)",(last_quote,last_quote,date.today(),ticker))
    cur.execute("UPDATE tx SET gain_loss = current_value-purchase_value")
    cur.execute("UPDATE tx SET percent_gain = (gain_loss/purchase_value)*100")
    conn.commit()
    cur.close()
    conn.close()



    
