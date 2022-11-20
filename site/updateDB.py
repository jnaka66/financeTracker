import yfinance as yf
import psycopg2
from datetime import date

def update_DB():
    conn = psycopg2.connect(user="jer",
                                    password="QASWEDFR1",
                                    host="localhost",
                                    port="5432",
                                    database="jer")
    cur = conn.cursor()
    cur.execute("Select distinct ticker from tx;")
    distinctTickersTuple=cur.fetchall()
    distinctTickers=[]
    for ticker in distinctTickersTuple:
        distinctTickers.append(ticker[0].strip())
    distinctTickers.remove("cash")
    prices = []
    for ticker in distinctTickers:
        curTicker = yf.Ticker(ticker)
        data = curTicker.history()
        last_quote = data['Close'].iloc[-1]
        prices.append(last_quote)
        cur.execute("UPDATE tx SET current_price = (%s), current_value = shares*(%s), last_update = (%s) where ticker=(%s)",(last_quote,last_quote,date.today(),ticker))
    cur.execute("UPDATE tx SET gain_loss = current_value-purchase_value")
    conn.commit()
    cur.close()
    conn.close()



    
