import psycopg2
from datetime import date
from psycopg2connection import *
import os
import csv
from psycopg2.extras import execute_values

def get_filenames():
    filenames = os.listdir('../incoming/')
    return [ filename for filename in filenames if str.lower(filename).endswith('.csv') ]

def read_files(filenames,conn,cur):
    for filename in filenames:
        insert_data = []
        #print(filename)
        with open('../incoming/'+filename, newline='') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            next(csvreader) #skip header
            if 'chase' in str.lower(filename):
                for row in csvreader:
                    #0Transaction Date,1Post Date,2Description,3Category,4Type,5Amount,Memo
                    #date formatting and remove negative for amount
                    tup = (row[0][-4:]+'-'+row[0][:2]+'-'+row[0][3:5],row[2],row[3],row[5][1:])
                    insert_data.append(tup)
            elif 'discover' in str.lower(filename):
                #print("discover")
                for row in csvreader:
                    #0Trans. Date,1Post Date,2Description,3Amount,4Category
                    #date formatting
                    tup = (row[0][-4:]+'-'+row[0][:2]+'-'+row[0][3:5],row[2],row[4],row[3])
                    insert_data.append(tup)
            else: #amex has a dumb filename activity.csv
                for row in csvreader:
                    #Date,Description,Amount
                    tup = (row[0][-4:]+'-'+row[0][:2]+'-'+row[0][3:5],row[1],row[2])
                    insert_data.append(tup)
                          
        #print(insert_data)
        execute_values(cur, "INSERT INTO stage.statement (date, description,amount) VALUES %s", insert_data)
                

def insert_DB():
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

def main():
    conn = psycopg2.connect(user=getpsycopg2User(),
                            password=getpsycopg2PW(),
                            host=getpsycopg2Host(),
                            port=getpsycopg2Port(),
                            database=getpsycopg2db())
    cur = conn.cursor()
    filenames = get_filenames()
    #print(filenames)
    read_files(filenames,conn,cur)
    conn.commit()
    cur.close()
    conn.close()
    


if __name__ == "__main__":
    main()

