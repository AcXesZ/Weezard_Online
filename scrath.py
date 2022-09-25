import csv

words = str('Ethos of Allentown')
print(words)

word_list = words.split(' ')
print(word_list)

with open('zipcodes.csv', 'r') as f_zips:
    zips = csv.reader(f_zips, delimiter=',')

    store_zip = None
    for line in zips:
        if store_zip is None:
            town = line[1]
            for word in word_list:
                word = word.upper()
                if 'OF' not in word:
                    if word.upper() in town:
                        store_zip = line[0]
                        print(store_zip)

