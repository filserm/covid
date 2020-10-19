import shelve


prev_inzidenz = shelve.open('inzidenz')

for k, item in prev_inzidenz.items():
    last_date = k
    prev_inzidenz_IN = item['IN'][1]
    prev_inzidenz_PAF = item['PAF'][1]
    prev_inzidenz_KEH = item['KEH'][1]
    prev_inzidenz_EI = item['EI'][1]
    print (item)

