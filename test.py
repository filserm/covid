import shelve
import os


path = os.path.join(os.path.expanduser("~/covid/"), 'inzidenz')
prev_inzidenz = shelve.open(path)

for k, item in prev_inzidenz.items():
    #print (k, item)
    pass


#     last_date = k
#     prev_inzidenz_IN = item['IN'][1]
#     prev_inzidenz_PAF = item['PAF'][1]
#     prev_inzidenz_KEH = item['KEH'][1]
#     prev_inzidenz_EI = item['EI'][1]
#     print (item)


path = os.path.join(os.path.expanduser("~/covid/"), 'fallzahlen')

prev_fallzahl = shelve.open(path)

for k, item in prev_fallzahl.items():
    print (k, item)

