import time
import sqlite3
import pandas as pd
import csv


start_time = time.time()

progress_Range = range(0, 9223372036854775807, 100000)

num_range = range(15001, 19640)
#num_range = range(15001, 15002)


'''with open('list.csv', 'w') as csvfile:
    csvfile.write('')


def process(df):
    print('im in')
    for index, row in df.iterrows():
        zip1 = int(row['zip1'])
        zip2 = int(row['zip2'])
        miles = float(row['mi_to_zcta5'])

        for num in num_range:
            if zip1 == num and zip2 in num_range and miles <= 50:

                #if zip1 == 15001:
                with open('list.csv', 'a', newline='') as csvfile:
                    # creating a csv writer object
                    csvwriter = csv.writer(csvfile)
                    # writing the fields
                    csvwriter.writerow([zip1, zip2, int(miles)])

chunksize = 10 ** 6
count = 0
with pd.read_csv('gaz2016zcta5distancemiles.csv', skiprows=range(1, 144569500), chunksize=chunksize) as reader:
    for chunk in reader:
        process(chunk)
'''

con = sqlite3.connect('main.db')
cur = con.cursor()
res = cur.execute("SELECT * FROM list_master WHERE zip1 = 18372 AND miles <= 20")
rowcount = res.rowcount

print(rowcount)
for row in res:
    print(row)
print("--- %s seconds ---" % (time.time() - start_time))


