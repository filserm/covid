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
        #data.append (html.find_all("td"))
        data.append (html.find_all("strong"))
        stand.append(html.find_all("p"))     
        
        hosp = str(data[0][0])
        index = hosp.index('>')
        hosp = hosp[index+1:]
        index = hosp.index('<')
        hosp = hosp[:index].strip().replace('.','')

        intensiv = str(data[0][1])
        index = intensiv.index('>')
        intensiv = intensiv[index+1:]
        index = intensiv.index('<')
        intensiv = intensiv[:index].strip().replace('.','')

        print ("intensivstation: ", intensiv)

        hosp_inz = str(data[0][1])[4:8].strip()

        last_update_kh = str(stand[0][8])
        index = last_update_kh.index(':')
        last_update_kh = last_update_kh[index+2:]
        index = last_update_kh.index('(')
        last_update_kh = last_update_kh[:index].strip()

        print ("last update kh: ", last_update_kh)

        if intensiv == 0:
            exit()
            
        data = {"krankenhaus" : hosp,
                "intensivstation": intensiv,
                "date": last_update_kh
        }

        return data, last_update_kh
        
    except Exception as error:
        hosp = "n/a"
        intensiv = "n/a"
        last_update_kh = "n/a"

def check_mongo(data, last_update_kh):
    try:
        #last_update_saved = mongodb.collection.find_one({"date": {"$exists": True}}, sort=[("date", -1)])["date"]
        for document in mongodb.collection.find():
            last_update_saved =document['date']

        print ("last update saved", last_update_saved, "last_update_kh", last_update_kh)
        if last_update_saved != last_update_kh:
            print ("inserting new data to mongodb")
            insert_mongo_db_document(data)
            return        
        else:
            print ("data already available or not available till now")
    except Exception as e:
        print ("error: ", e)
        

def main():
    data, last_update_kh = get_hospitalisierung()
    check_mongo(data, last_update_kh)
    

main()
