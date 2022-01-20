import json
from datetime import datetime as dt, timedelta
import pandas as pd
import requests
import os
import shelve
import ssl
import dateutil.parser
from b2blaze import B2
from bs4 import BeautifulSoup #pip install beautifulsoup4
from mongo_db_insert import Mongo
import time
import socket
from modules.api import Api

hostname = socket.gethostname()
ssl._create_default_https_context = ssl._create_unverified_context

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

global smiley
spritze = "\\U0001F489".encode("latin_1")
smiley = (spritze.decode("raw_unicode_escape").encode('utf-16', 'surrogatepass').decode('utf-16'))


#county data
url = r'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=county%20%3D%20%27SK%20INGOLSTADT%27%20OR%20county%20%3D%20%27LK%20DACHAU%27%20OR%20county%20%3D%20%27LK%20EICHST%C3%84TT%27%20OR%20county%20%3D%20%27LK%20PFAFFENHOFEN%20A.D.ILM%27%20OR%20county%20%3D%20%27LK%20KELHEIM%27&outFields=county,cases7_per_100k,last_update&returnGeometry=false&outSR=4326&f=json'

#germany data - marlon lückert
rki_url = 'https://api.corona-zahlen.org/germany/'
rki_url_history = 'https://api.corona-zahlen.org/germany/history/cases'
rki_url_history = 'https://api.corona-zahlen.org/germany/history/incidence'

#vaccine data
vaccine_url = 'https://api.corona-zahlen.org/vaccinations'

#intensivstation
intensiv_url = 'https://europe-west3-brdata-corona.cloudfunctions.net/diviApi/query?area=BY&indicator=Patienten&filetype=json'

now = dt.now()
now = now.strftime("%d.%m.%Y, %H:%M Uhr") 

wappen = {
            'IN': 'https://f003.backblazeb2.com/file/coviddata/Ingolstadt.png' ,
            'PAF': 'https://f003.backblazeb2.com/file/coviddata/pfaffenhofen..png' ,
            'DAH': 'https://f003.backblazeb2.com/file/coviddata/dachau.png' ,
            'KEH': 'https://f003.backblazeb2.com/file/coviddata/kelheim.png' ,
            'EI': 'https://f003.backblazeb2.com/file/coviddata/eichstaett.png' ,
}


def get_rki_history():
    api_instance = Api(rki_url_history)
    api_instance.set_session()
    r = api_instance.parse_response()
    datesarr, dataarr = [], []
    for item in r.items():
        if item[0] == 'data':
            for elem in item[1]:
                #dataarr.append(str(int(elem['cases'])))
                dataarr.append(str(int(elem['weekIncidence'])))
                datesarr.append(str(elem['date']))
    return dataarr, datesarr

def get_intensiv():
    api_instance = Api(intensiv_url)
    api_instance.set_session()
    r = api_instance.parse_response()
    idatesarr, idataarr = [], []
    for item in r:
        idataarr.append(str(int(item['faelleCovidAktuell'])))
        idatesarr.append(str(item['date']))
    return idataarr, idatesarr

def get_hospitalisierung():
    mongodb = Mongo(
        cluster = 'cluster0.tr5bj.mongodb.net'
        , database = 'covid'
        , collection = 'hospital'
    )
    mongodb.connect()

    hosp, intensiv, datum = [], [], []

    try:
        cursor = mongodb.collection.find({})
        count_documents = int(mongodb.collection.count_documents({}))
        
        i, hosp_yesterday, intensiv_yesterday=0,0,0
        for document in cursor:
            i += 1
            if i == count_documents-1:
                hosp_yesterday     = int(document['krankenhaus'])
                intensiv_yesterday = int(document['intensivstation'])

            hosp.append(document['krankenhaus'])
            intensiv.append(document['intensivstation'])
            datum.append(document['date'])
            hosp_diff_yesterday     = int(document['krankenhaus']) - hosp_yesterday
            intensiv_diff_yesterday = int(document['intensivstation']) - intensiv_yesterday

        return hosp, intensiv, datum, hosp_diff_yesterday, intensiv_diff_yesterday

    except Exception as e:
        print (e)

    

def replace_comma(a):
    return a.replace(',','.')

def replace_dot(a):
    return a.replace('.',',')

def retrieve_vaccine_data():
    global vaccine_record, last_update_vaccine_formated

    api_instance = Api(vaccine_url)
    api_instance.set_session()
    vaccine = api_instance.parse_response()

    last_update_vaccine = vaccine.meta.lastUpdate
    last_update_vaccine = dateutil.parser.parse(last_update_vaccine)
    last_update_vaccine_formated = last_update_vaccine.strftime("%d.%m.%Y, %H:%M Uhr")
    #print (last_update_vaccine_formated)

    last_update_vaccine      = str(last_update_vaccine)
    de_vaccine_total = vaccine.data.vaccinated
    de_vaccine_delta = vaccine.data.delta
    de_vaccine_quote = vaccine.data.quote * 100.00
    by_vaccine_total = vaccine.data.states.BY.vaccinated
    by_vaccine_delta = vaccine.data.states.BY.delta
    by_vaccine_quote = vaccine.data.states.BY.quote *100.00

    de_vaccine_second_total = vaccine.data.secondVaccination.vaccinated
    de_vaccine_second_delta = vaccine.data.secondVaccination.delta
    de_vaccine_second_quote = vaccine.data.secondVaccination.quote * 100.00

    by_vaccine_second_total = vaccine.data.states.BY.secondVaccination.vaccinated
    by_vaccine_second_delta = vaccine.data.states.BY.secondVaccination.delta
    by_vaccine_second_quote = vaccine.data.states.BY.secondVaccination.quote * 100.00

    de_vaccine_booster_total = vaccine.data.boosterVaccination.vaccinated
    de_vaccine_booster_delta = vaccine.data.boosterVaccination.delta
    de_vaccine_booster_quote = vaccine.data.boosterVaccination.quote * 100.00

    by_vaccine_booster_total = vaccine.data.states.BY.boosterVaccination.vaccinated
    by_vaccine_booster_delta = vaccine.data.states.BY.boosterVaccination.delta
    by_vaccine_booster_quote = vaccine.data.states.BY.boosterVaccination.quote * 100.00

    de_vaccine_total = replace_comma(f'{de_vaccine_total:,}')
    try:
        de_vaccine_delta = replace_comma(f'{de_vaccine_delta:,}')
    except: 
        de_vaccine_delta = 'unkown'
    by_vaccine_total = replace_comma(f'{by_vaccine_total:,}')
    try:
        by_vaccine_delta = replace_comma(f'{by_vaccine_delta:,}')
    except:
        by_vaccine_delta = 'unkown'
    de_vaccine_quote = replace_dot(format(de_vaccine_quote, '.2f')+'%')   
    by_vaccine_quote = replace_dot(format(by_vaccine_quote, '.2f')+'%')

    de_vaccine_second_total = replace_comma(f'{de_vaccine_second_total:,}')
    de_vaccine_second_delta = replace_comma(f'{de_vaccine_second_delta:,}')
    de_vaccine_second_quote = replace_dot(format(de_vaccine_second_quote, '.2f')+'%')
    by_vaccine_second_total = replace_comma(f'{by_vaccine_second_total:,}')
    by_vaccine_second_delta = replace_comma(f'{by_vaccine_second_delta:,}')
    by_vaccine_second_quote = replace_dot(format(by_vaccine_second_quote, '.2f')+'%')

    try:
        de_vaccine_booster_total = replace_comma(f'{de_vaccine_booster_total:,}')
    except:
        de_vaccine_booster_total = 'unkown'
    de_vaccine_booster_delta = replace_comma(f'{de_vaccine_booster_delta:,}')
    de_vaccine_booster_quote = replace_dot(format(de_vaccine_booster_quote, '.2f')+'%')
    try:
        by_vaccine_booster_total = replace_comma(f'{by_vaccine_booster_total:,}')
    except:
        by_vaccine_booster_total = 'unknown'
    by_vaccine_booster_delta = replace_comma(f'{by_vaccine_booster_delta:,}')
    by_vaccine_booster_quote = replace_dot(format(by_vaccine_booster_quote, '.2f')+'%')

    #print (last_update, de_vaccine_total, de_vaccine_delta, by_vaccine_total, by_vaccine_delta)
    global vaccine_dict
    vaccine_dict = {}
    vaccine_dict['DE'] = [de_vaccine_total, de_vaccine_delta, de_vaccine_quote, de_vaccine_second_total, de_vaccine_second_delta, de_vaccine_second_quote, de_vaccine_booster_total, de_vaccine_booster_delta, de_vaccine_booster_quote]
    vaccine_dict['BY'] = [by_vaccine_total, by_vaccine_delta, by_vaccine_quote, by_vaccine_second_total, by_vaccine_second_delta, by_vaccine_second_quote, by_vaccine_booster_total, by_vaccine_booster_delta, by_vaccine_booster_quote]

    path = os.path.join(os.path.expanduser("~/covid/"), 'vaccine_db')
    with shelve.open(path) as db:
        db[last_update_vaccine]=vaccine_dict
       
    vaccineDB = shelve.open(path)

    for k, item in sorted(vaccineDB.items(), key=lambda x: (dt.strptime(x[0][:10], '%Y-%m-%d')), reverse=True):
        #print ("Datum", k, "item", item)
        vaccine_record =  item
        #print (k, vaccine_record)
    

def retrieve_covid_data():
 
    data = pd.DataFrame([])
    data = pd.read_json(url, lines=True)

    global de_rki, de_rki_delta

    #try it 15 times
    for i in range(1,16):                   
        try:
            print (f'try - {i} ...') 
            api_instance = Api(rki_url)
            api_instance.set_session()
            r = api_instance.parse_response()
            de_rki          = r.cases
            de_rki_delta    = r.delta.cases
            if type(de_rki_delta) == int:
                break
        except Exception as e:
            print ("sleep 10 sec", e)
            time.sleep(10)
            next
        #set to "nicht verfügbar", if all 5 trys went bad
        de_rki = "null"
        de_rki_delta = "nicht verfügbar"

    print (f'new cases: {de_rki_delta} - cases total: {de_rki}')
    
    global inzidenz_dict
    inzidenz_dict = {}
    ingo = pd.Series(data['features']) 
    data['countyIN'] = ingo.iloc[0][0]['attributes']['county'][3:]
    data['last_updateIN'] = ingo.iloc[0][0]['attributes']['last_update']
    data['cases7_per_100kIN'] = ingo.iloc[0][0]['attributes']['cases7_per_100k']

    data['countyPAF'] = ingo.iloc[0][1]['attributes']['county'][3:]
    data['last_updatePAF'] = ingo.iloc[0][1]['attributes']['last_update']
    data['cases7_per_100kPAF'] = ingo.iloc[0][1]['attributes']['cases7_per_100k']

    data['countyKEH'] = ingo.iloc[0][2]['attributes']['county'][3:]
    data['last_updateKEH'] = ingo.iloc[0][2]['attributes']['last_update']
    data['cases7_per_100kKEH'] = ingo.iloc[0][2]['attributes']['cases7_per_100k']

    data['countyEI'] = ingo.iloc[0][3]['attributes']['county'][3:]
    data['last_updateEI'] = ingo.iloc[0][3]['attributes']['last_update']
    data['cases7_per_100kEI'] = ingo.iloc[0][3]['attributes']['cases7_per_100k']

    data['countyDAH'] = ingo.iloc[0][4]['attributes']['county'][3:]
    data['last_updateDAH'] = ingo.iloc[0][4]['attributes']['last_update']
    data['cases7_per_100kDAH'] = ingo.iloc[0][4]['attributes']['cases7_per_100k']

    inzidenz_dict['IN'] = [str (data['countyIN'][0]), str(data['cases7_per_100kIN'][0])[:5], str(data['last_updateIN'][0])]
    inzidenz_dict['PAF'] = [str (data['countyPAF'][0]), str(data['cases7_per_100kPAF'][0])[:5], str(data['last_updatePAF'][0])]
    inzidenz_dict['KEH'] = [str (data['countyKEH'][0]), str(data['cases7_per_100kKEH'][0])[:5], str(data['last_updateKEH'][0])]
    inzidenz_dict['EI'] = [str (data['countyEI'][0]), str(data['cases7_per_100kEI'][0])[:5], str(data['last_updateEI'][0])]
    inzidenz_dict['DAH'] = [str (data['countyDAH'][0]), str(data['cases7_per_100kDAH'][0])[:5], str(data['last_updateDAH'][0])]

    last_update = ingo.iloc[0][0]['attributes']['last_update']

    path = os.path.join(os.path.expanduser("~/covid/"), 'inzidenz')
    #shelve.open(path)
    #with shelve.open('inzidenz') as db:
    with shelve.open(path) as db:
        #print ("key:", last_update)
        #print ("value:", inzidenz_dict)
        db[last_update]=inzidenz_dict
    
    
    prev_inzidenz = shelve.open(path)

    for k, item in sorted(prev_inzidenz.items(), key=lambda x: (dt.strptime(x[0][:10], '%d.%m.%Y')), reverse=True):
        #print ("Datum", k)
        if k != last_update:
            print (last_update)
            prev_inzidenz_IN = item['IN'][1]
            prev_inzidenz_PAF = item['PAF'][1]
            prev_inzidenz_KEH = item['KEH'][1]
            prev_inzidenz_EI = item['EI'][1]
            #prev_inzidenz_DAH = item['DAH'][1]
            if last_update == '04.12.2021, 00:00 Uhr':
                prev_inzidenz_DAH = 410.8
                prev_inzidenz_IN = 570.2
                prev_inzidenz_KEH = 498.5
                prev_inzidenz_EI = 559.4
                prev_inzidenz_PAF = 545.3

            else:
                prev_inzidenz_DAH = item['DAH'][1]

            break

    #print ("heute", round(float(inzidenz_dict['IN'][1])))
    #print ("gestern", float(prev_inzidenz_IN), 2)
    
    diff_IN  = round(float(inzidenz_dict['IN'][1])  - float(prev_inzidenz_IN), 2)
    diff_PAF = round(float(inzidenz_dict['PAF'][1]) - float(prev_inzidenz_PAF),2)
    diff_KEH = round(float(inzidenz_dict['KEH'][1]) - float(prev_inzidenz_KEH),2)
    diff_EI  = round(float(inzidenz_dict['EI'][1])  - float(prev_inzidenz_EI), 2)
    diff_DAH  = round(float(inzidenz_dict['DAH'][1])  - float(prev_inzidenz_DAH), 2)
    #print (diff_IN)
    
    inzidenz_dict['IN'] = inzidenz_dict['IN'] + [diff_IN]
    inzidenz_dict['PAF'] = inzidenz_dict['PAF'] + [diff_PAF]
    inzidenz_dict['KEH'] = inzidenz_dict['KEH'] + [diff_KEH]
    inzidenz_dict['EI'] = inzidenz_dict['EI'] + [diff_EI]
    inzidenz_dict['DAH'] = inzidenz_dict['DAH'] + [diff_DAH]

    #fuer die RKI Zahlen 
    global fallzahlen_dict
    fallzahlen_dict = {}
    #fallzahlen_dict['DE'] = [str('07.11.2020, 00:00 Uhr'), str (600000)]
    fallzahlen_dict['DE'] = [str(last_update), str (de_rki)]

    path = os.path.join(os.path.expanduser("~/covid/"), 'fallzahlen')
    with shelve.open(path) as db:
        db[last_update]=fallzahlen_dict
        #db['07.11.2020, 00:00 Uhr']=fallzahlen_dict
    
    prev_fallzahl = shelve.open(path)
    for k, item in sorted(prev_fallzahl.items(), key=lambda x: (dt.strptime(x[0][:10], '%d.%m.%Y')), reverse=True):
        #print ("Datum", k, "last_update", last_update)
        if k != last_update:
            #print ("asf")
            prev_fallzahl_DE = item['DE'][1]
            #prev_fallzahl_BY = item['BY'][1]
            break
    
def upload_html_b2():    
    b2 = B2()
    bucket = b2.buckets.get('coviddata')

    chart_file = open(chart_filename, 'rb')
    chart_file_rki = open(chart_filename_rki, 'rb')
    try:
        bucket.files.upload(contents=chart_file, file_name=chart_out_filename)
        bucket.files.upload(contents=chart_file_rki, file_name=chart_rki_out_filename)
    except Exception as error:
        print ("error: ", error)

    text_file = open(html_filename, 'rb')
    bucket.files.upload(contents=text_file, file_name=html_out_filename)

def chart_html(hosp, intensiv, datum):
     
    datum    = ','.join(f'"{w}"' for w in datum)
    intensiv = ','.join(intensiv)
    hosp     = ','.join(hosp)

    chart_template = os.path.join(os.path.expanduser("~/covid/html_template"), 'chart_template.html')
    chart_template_file = open(chart_template, 'r')
    chart_code = chart_template_file.readlines()

    global chart_out_filename, chart_filename
    chart_out_filename = 'chart1.html'
    chart_filename = os.path.join(os.path.expanduser("~/covid/html_output"), chart_out_filename)
    chartfile = open (chart_filename, 'w')

    for item in chart_code:
        if item.find('##DATUMSWERTE##') > 0:
            item = item.replace('##DATUMSWERTE##', datum)
        if item.find('##INTENSIV##') > 0:
            item = item.replace('##INTENSIV##', intensiv)
        if item.find('##HOSPITAL##') > 0:
            item = item.replace('##HOSPITAL##', hosp)
        
        chartfile.write(item)
    chartfile.close()


def chart_rki(dataarr, datesarr):
    data  = ','.join(dataarr)
    dates = ','.join(f'"{w}"' for w in datesarr)

    chart_rki_history_template = os.path.join(os.path.expanduser("~/covid/html_template"), 'chart_rki_history_template.html')
    chart_rki_history_template_file = open(chart_rki_history_template, 'r')
    chart_code = chart_rki_history_template_file.readlines()

    global chart_rki_out_filename, chart_filename_rki
    chart_rki_out_filename = 'chart_rki.html'
    chart_filename_rki = os.path.join(os.path.expanduser("~/covid/html_output"), chart_rki_out_filename)
    chartfile = open (chart_filename_rki, 'w')

    for item in chart_code:
        if item.find('##DATUMSWERTE##') > 0:
            item = item.replace('##DATUMSWERTE##', dates)
        if item.find('##RKI_HISTORY##') > 0:
            item = item.replace('##RKI_HISTORY##', data)
        
        chartfile.write(item)
    chartfile.close()


def html(hosp, intensiv, last_update_kh, hosp_diff_yesterday, intensiv_diff_yesterday):

    print ("hospi:", hosp, "intensiv", intensiv)
    
    add_line, new_line_hosp =  [], []
    i = 1
    html_template = os.path.join(os.path.expanduser("~/covid/html_template"), 'covid_html_template.html')
    html_template_file = open(html_template, 'r')
    html_code = html_template_file.readlines()

    global html_out_filename, html_filename
    html_out_filename = 'covid.html'
    html_filename = os.path.join(os.path.expanduser("~/covid/html_output"), html_out_filename)
    htmlfile = open (html_filename, 'w')

    for item in html_code:
        if item.find('##HOSPITALISIERUNG##') > 0:

            green = '#56f86b'
            try:
                if int (intensiv) > 600:
                    text_color_intensiv = "red"
                    text_color_hosp = "red"
                elif int (hosp) > 1200 or int (intensiv) > 450:
                    text_color_hosp = "yellow"
                    text_color_intensiv = "yellow"
                else:
                    text_color_hosp = green
                    text_color_intensiv = green
            except:
                text_color_hosp = green
                text_color_intensiv = green
            
            if hosp_diff_yesterday > 0:
                hosp_diff_yesterday = '+' + str(hosp_diff_yesterday)
            if intensiv_diff_yesterday > 0:
                intensiv_diff_yesterday = '+' + str(intensiv_diff_yesterday)

            new_line_hosp.append(f'''
                       
            <tr>
                <td colspan = 1 style="text-align:left"><img src="https://f003.backblazeb2.com/file/coviddata/hospital.png" class="kh_logo"></td>
                <td colspan = 1 >Neuaufnahmen Krankenhaus (7 Tage)</td>
                <td colspan = 2 style="line-height: 1; text-align: left; font-size: 20px; color:{text_color_hosp}">{hosp} <p2>{hosp_diff_yesterday}</p2></td>
                <td colspan = 1 style="font-size: 10px !important; color:yellow !important;">> 1.200</td>
            </tr>     
            <tr>
                <td colspan = 1 style="text-align:center"><img src="https://f003.backblazeb2.com/file/coviddata/icu.png" class="kh_logo"></td>
                <td colspan = 1 >Patienten auf Intensivstation</td>                
                <td colspan = 2 style="line-height: 1; font-size: 20px; text-align:left; color:{text_color_intensiv}">{intensiv} <p2>{intensiv_diff_yesterday}</p2></td>
                <td colspan = 1 style="font-size: 10px !important; color: yellow !important">> 450<br><span1 style="font-size: 10px !important; color: red !important">> 600</span1></td>
            </tr>            
            ''')

            #new_line_hosp.append(f'<tr><td colspan = 13 style="font-size: 10px !important; text-align:right !important; ">letzte Aktualisierung {last_update_kh}</td></tr>')
            new_line = ''.join(new_line_hosp)
            item = item.replace('##HOSPITALISIERUNG##', new_line)
             

        if item.find('##COVID_DATA##') > 0:
            for k, v in sorted(inzidenz_dict.items(), key=lambda x: float(x[1][1]), reverse=True):
                add_line.append('<tr>')
                #add_line.append(f'<td class="text-align:center;">{i}</td>')               
                add_line.append(f'<td colspan = 1 style="text-align:center"><img src={wappen[k]} class="wappen"></td>')

                county = inzidenz_dict[k][0]
                inzidenz = inzidenz_dict[k][1]
                inzidenz_vortag = inzidenz_dict[k][3]
                last_update = inzidenz_dict[k][2]
                new_inzidenz_obj = Inzidenz(county, inzidenz, inzidenz_vortag, last_update)
                new_line = new_inzidenz_obj.htmlcode()
                add_line.append(new_line)     
                add_line.append('</tr>')     
                i+=1
            new_line = ''.join(add_line)
            #print (new_line, "\n")

            item = item.replace('##COVID_DATA##', new_line)
        if item.find('##RKI##') >0:
            
            item = item.replace('##RKI##' , f'''
                   
                    <tr><td colspan = 6 style=text-align:center important!;">
                            <div style="font-size: 18px !important;
                                        
                                        color: white;
                                        background-color: lightgrey;
                                        margin-top: 25px;
                                        //margin-bottom: 30px;
                                        margin-left: 20px;
                                        margin-right: 20px;
                                        width:auto;
                                        height:70px; 
                                        //border-style: ridge; 
                                        border-color: red;
                                        //padding: 10px;
                                        ">
                                    Neuinfektionen DE
                            <br><span>{de_rki_delta}</span><br></td></div></tr>
                            </td> 
                    
                              
                    '''
                    )
           
       
        if item.find('##LAST_UPDATE##') > 0:
            item = item.replace('##LAST_UPDATE##' ,f'<tr><td colspan = 6 style="font-size: 10px !important; text-align:right !important; ">letzte Aktualisierung RKI {last_update}</td></tr>')
        
        if item.find('##VACCINE_HEADER##') >0:
            item = item.replace('##VACCINE_HEADER##' ,f"""
                        
                        <th colspan = 2></th>
                        <th class="logo" colspan = 2 style="text-align:center"><img src="https://img.icons8.com/emoji/48/000000/germany-emoji.png" class="flags"> </th>
                        <th colspan = 2 style="text-align:center"><img src="https://f003.backblazeb2.com/file/coviddata/bavaria.png" class="flags1"> </th>
                        
                        """)

        if item.find('##VACCINE##') >0:
            item = item.replace('##VACCINE##' ,f"""
                    
                        <tr>
                            <td colspan = 2>Erstimpfung<p> </p></td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['DE'][0]}<br><p1> +{vaccine_dict['DE'][1]}</p><br><p>{vaccine_dict['DE'][2]}</p></td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['BY'][0]}<br><p1> +{vaccine_dict['BY'][1]}</p><br><p>{vaccine_dict['BY'][2]}</p></td>
                        </tr>
                        <tr>
                            <td colspan = 2>Zweitimpfung<p> </p></td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['DE'][3]}<br><p1> +{vaccine_dict['DE'][4]}</p><br><p>{vaccine_dict['DE'][5]}</p></td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['BY'][3]}<br><p1> +{vaccine_dict['BY'][4]}</p><br><p>{vaccine_dict['BY'][5]}</p></td>
                        </tr>
                        <tr>
                            <td colspan = 2>Boosterimpfung<p> </p></td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['DE'][6]}<br><p1> +{vaccine_dict['DE'][7]}</p><br><p>{vaccine_dict['DE'][8]}</p></td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['BY'][6]}<br><p1> +{vaccine_dict['BY'][7]}</p><br><p>{vaccine_dict['BY'][8]}</p></td>
                        </tr>
                        <tr>
                            <td colspan =  6 style="font-size: 10px !important; text-align:right !important;">letzte Aktualisierung RKI {last_update_vaccine_formated}<br>letzter Check {now}</td>
                           
                            
                        </tr>
                      

            
                        """)
       
        htmlfile.write(item)
    htmlfile.close()

class Inzidenz():
    def __init__(self, county, inzidenz, inzidenz_vortag, last_update):
        self.county = county
        self.inzidenz = inzidenz
        self.inzidenz_out = '{:>7}'.format(str(inzidenz)).replace('.',',')
        self.inzidenz_vortag = inzidenz_vortag
        self.inzidenz_vortag_out = format(inzidenz_vortag, '.2f')
        self.inzidenz_vortag_out = '{:>7}'.format(str(inzidenz_vortag)).replace('.',',')

    def htmlcode(self):
        #print (self.county, self.inzidenz, self.last_update)
        #self.inzidenz_vortag = -10
        if self.inzidenz_vortag > 0:
            # add_arrow = '\n<img src="https://f003.backblazeb2.com/file/coviddata/red_up.png" class="arrow">\n'
            add_arrow = '\n<span class="arrow arrow-top"></span>\n'
            arrow = "up"
            effect = 'font-effect-fire-animation'
        elif self.inzidenz_vortag < 0:
            #add_arrow = '\n<img src="https://f003.backblazeb2.com/file/coviddata/green_down.png" class="arrow">\n'
            add_arrow = '\n<span class="arrow arrow-down"></span>\n'
            arrow = "down"
            #color_gn = '#56f86b'
            effect = ''
        elif self.inzidenz_vortag == 0:
            add_arrow = '\n<span class="line"></span>\n'
            arrow = 'up'
            effect = ''
        if float(self.inzidenz) >= 100.00:
            #color = '#ff0000'
            color = 'red'
            #textcolor = 'white'
        elif 50.00 <= float(self.inzidenz) < 100.00:
            color = '#f00148'
            #textcolor = 'white'
        elif 35.00 <= float(self.inzidenz) < 50.00:
            color = 'orange'
            #textcolor = 'white'
        elif float(self.inzidenz) < 35.00:
            color = '#56f86b'
            #textcolor = 'black'

        if arrow == "up":
            return f'<td>{self.county}</td> <td style="color:{color} !important;"><strong>{self.inzidenz_out}</strong></td><td class={effect} style=text-align:right important!>{self.inzidenz_vortag_out} </td><td colspan=2>{add_arrow}</td>'
            #return f'<td>{self.county}</td> <td style="color:{color} !important;"><strong>{self.inzidenz_out}</strong></td><td colspan=2 class={effect} style=text-align:center important!>+ {self.inzidenz_vortag_out} </td>'
        
        elif arrow == "down":
            return f'<td>{self.county}</td> <td style="color:{color} !important;"><strong>{self.inzidenz_out}</strong></td><td style=text-align:right important!>{self.inzidenz_vortag_out}</td><td colspan=2>{add_arrow}</td>'
            #return f'<td>{self.county}</td> <td style="color:{color} !important;"><strong>{self.inzidenz_out}</strong></td><td colspan=2 style="color:{color_gn} !important; text-align:center important!">- {self.inzidenz_vortag_out} </td>'


def main():
    hosp, intensiv, datum, hosp_diff_yesterday, intensiv_diff_yesterday = get_hospitalisierung()
    #chart_html(hosp, intensiv, datum)
    
    idataarr, idatesarr = get_intensiv()
    chart_html([], idataarr, idatesarr)
    dataarr, datesarr = get_rki_history()
    chart_rki(dataarr, datesarr)

    retrieve_covid_data()
    retrieve_vaccine_data()
    
    html(hosp[-1], intensiv[-1], datum[-1], hosp_diff_yesterday, intensiv_diff_yesterday)
    
    if 'rasp' in hostname:
        #upload only on raspberry
        upload_html_b2() #backblaze bucket
    else:
        pass
    


main()


