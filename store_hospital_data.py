from mongo_db_insert import Mongo
import datetime
import requests
from bs4 import BeautifulSoup #pip install beautifulsoup4


today     = datetime.date.today()
today     = today.strftime("%d.%m.%Y")
print (today)

global mongodb

mongodb = Mongo(
        cluster = 'cluster0.tr5bj.mongodb.net'
        , database = 'covid'
        , collection = 'hospital'
    )
mongodb.connect()

def insert_mongo_db_document(data):
    mongodb.insert(data)

def get_hospitalisierung():
    global hosp, hosp_inz, intensiv, last_update_kh
    data = []
    stand = []

    try:
        url = 'https://www.lgl.bayern.de/gesundheit/infektionsschutz/infektionskrankheiten_a_z/coronavirus/karte_coronavirus/index.htm#kennzahlen'
        req = requests.get(url)
        html = BeautifulSoup(req.content, 'html.parser')
        #print(soup.prettify())
        data.append (html.find_all("td"))
        stand.append(html.find_all("p"))
        
        hosp = str(data[0][1])
        hosp_inz = str(data[0][3])
        intensiv = str(data[0][13])

        index = hosp.index('>')
        hosp = hosp[index+1:]
        index = hosp.index('<')
        hosp = hosp[:index]
        
        index = intensiv.index('>')
        intensiv = intensiv[index+1:]
        index = intensiv.index('<')
        intensiv = intensiv[:index]
        #print (hosp)

        last_update_kh = str(stand[0][8])

        #print (last_update_kh)

        index = last_update_kh.index('Stand: ')
        last_update_kh = last_update_kh[index+6:]
        index = last_update_kh.index(',')
        last_update_kh = last_update_kh[:index]
        last_update_kh = last_update_kh.strip()

        #index = last_update_kh.index('<')
        #last_update_kh = last_update_kh[:index-1]
        #print ("last update: ", last_update_kh)

        data = {"krankenhaus" : hosp,
                "intensivstation": intensiv,
                "date": last_update_kh
        }

        return data, last_update_kh
        
    except Exception as error:
        hosp = "n/a"
        intensiv = "n/a"
        last_update_kh = "n/a"

def check_mongo(last_update_kh):
    try:
        last_update_saved = mongodb.collection.find_one({"date": {"$exists": True}}, sort=[("date", -1)])["date"]

        print ("last update saved", last_update_saved, "last_update_kh", last_update_kh)
        if last_update_saved != last_update_kh:
            return        
        else:
            print ("data already available or not available till now")
            exit()
    except:
        return
        

def main():
    data, last_update_kh = get_hospitalisierung()
    check_mongo(last_update_kh)
    insert_mongo_db_document(data)

main()
