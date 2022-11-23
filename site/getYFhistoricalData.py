import yfinance as yf
from datetime import date

def getYFhistoricalData(ticker,dateSince):
    yticker = yf.Ticker(ticker)
    print(dateSince,date.today())
    #data = yf.download(ticker,start = dateSince, end = date.today())
    #print(data)
    penis=0
    return penis
