import json
from datetime import datetime as dt, timedelta
from pprint import pprint
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import numpy as np
from pylab import figure, text, scatter, show
import re
import subprocess
from requests.auth import HTTPBasicAuth
import requests
import os
import shelve
import ssl
#import locale
import dateutil.parser
from b2blaze import B2
#set environment variables B2_KEY_ID and B2_APPLICATION_KEY
from bs4 import BeautifulSoup #pip install beautifulsoup4
from mongo_db_insert import Mongo
import time
import socket
from modules.api import Api

hostname = socket.gethostname()
ssl._create_default_https_context = ssl._create_unverified_context
#, cafile="/vagrant/certs/selfsigned.crt"

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


url = 'https://api.covid19api.com/dayone/country/germany'
url_IN = r'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=county%20%3D%20%27SK%20INGOLSTADT%27%20OR%20county%20%3D%20%27LK%20DACHAU%27%20OR%20county%20%3D%20%27LK%20EICHST%C3%84TT%27%20OR%20county%20%3D%20%27LK%20PFAFFENHOFEN%20A.D.ILM%27%20OR%20county%20%3D%20%27LK%20KELHEIM%27&outFields=county,cases7_per_100k,last_update&returnGeometry=false&outSR=4326&f=json'

rki_url = 'https://api.corona-zahlen.org/germany'
vaccine_url = 'https://api.corona-zahlen.org/vaccinations'

days = 14
rolling_window_avg = 7
now = dt.now()

now = now.strftime("%d.%m.%Y, %H:%M Uhr") 

wappen = {
            'IN': 'https://f003.backblazeb2.com/file/coviddata/Ingolstadt.png' ,
            'PAF': 'https://f003.backblazeb2.com/file/coviddata/pfaffenhofen..png' ,
            'DAH': 'https://f003.backblazeb2.com/file/coviddata/dachau.png' ,
            'KEH': 'https://f003.backblazeb2.com/file/coviddata/kelheim.png' ,
            'EI': 'https://f003.backblazeb2.com/file/coviddata/eichstaett.png' ,

}

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
        for document in cursor:
          hosp.append(document['krankenhaus'])
          intensiv.append(document['intensivstation'])
          datum.append(document['date'])
        return hosp, intensiv, datum

    except Exception as e:
        print (e)

    
def retrieve_vaccine_data():
    global vaccine_record, last_update_vaccine_formated

    data = s = requests.Session()
    resp = s.get(vaccine_url)
    vaccine = resp.json()
    last_update_vaccine      = vaccine['meta']['lastUpdate']
    last_update_vaccine      = dateutil.parser.parse(last_update_vaccine)
    last_update_vaccine_formated = last_update_vaccine.strftime("%d.%m.%Y, %H:%M Uhr")
    #print (last_update_vaccine_formated)

    last_update_vaccine      = str(last_update_vaccine)
    de_vaccine_total = vaccine['data']['vaccinated']
    de_vaccine_delta = vaccine['data']['delta']
    de_vaccine_quote = vaccine['data']['quote']
    by_vaccine_total = vaccine['data']['states']['BY']['vaccinated']
    by_vaccine_delta = vaccine['data']['states']['BY']['delta']
    by_vaccine_quote = vaccine['data']['states']['BY']['quote']
    last_checked = vaccine['data']['states']['BY']['delta']

    de_vaccine_second_total = vaccine['data']['secondVaccination']['vaccinated']
    de_vaccine_second_delta = vaccine['data']['secondVaccination']['delta']
    de_vaccine_second_quote = vaccine['data']['secondVaccination']['quote']

    by_vaccine_second_total = vaccine['data']['states']['BY']['secondVaccination']['vaccinated']
    by_vaccine_second_delta = vaccine['data']['states']['BY']['secondVaccination']['delta']
    by_vaccine_second_quote = vaccine['data']['states']['BY']['secondVaccination']['quote']

    de_vaccine_total = f'{de_vaccine_total:,}'
    de_vaccine_total = de_vaccine_total.replace(',','.')

    de_vaccine_delta = f'{de_vaccine_delta:,}'
    de_vaccine_delta = de_vaccine_delta.replace(',','.')

    by_vaccine_total = f'{by_vaccine_total:,}'
    by_vaccine_total = by_vaccine_total.replace(',','.')

    by_vaccine_delta = f'{by_vaccine_delta:,}'
    by_vaccine_delta = by_vaccine_delta.replace(',','.')

    de_vaccine_quote = de_vaccine_quote * 100.00
    de_vaccine_quote = format(de_vaccine_quote, '.2f').replace('.',',')+'%'
    
    by_vaccine_quote = by_vaccine_quote * 100.00
    by_vaccine_quote = format(by_vaccine_quote, '.2f').replace('.',',')+'%'


    de_vaccine_second_total = f'{de_vaccine_second_total:,}'
    de_vaccine_second_total = de_vaccine_second_total.replace(',','.')

    de_vaccine_second_delta = f'{de_vaccine_second_delta:,}'
    de_vaccine_second_delta = de_vaccine_second_delta.replace(',','.')
    
    de_vaccine_second_quote = de_vaccine_second_quote * 100.00
    de_vaccine_second_quote = format(de_vaccine_second_quote, '.2f').replace('.',',')+'%'


    by_vaccine_second_total = f'{by_vaccine_second_total:,}'
    by_vaccine_second_total = by_vaccine_second_total.replace(',','.')

    by_vaccine_second_delta = f'{by_vaccine_second_delta:,}'
    by_vaccine_second_delta = by_vaccine_second_delta.replace(',','.')
    
    by_vaccine_second_quote = by_vaccine_second_quote * 100.00
    by_vaccine_second_quote = format(by_vaccine_second_quote, '.2f').replace('.',',')+'%'

    #print (last_update, de_vaccine_total, de_vaccine_delta, by_vaccine_total, by_vaccine_delta)
    global vaccine_dict
    vaccine_dict = {}
    vaccine_dict['DE'] = [de_vaccine_total, de_vaccine_delta, de_vaccine_quote, de_vaccine_second_total, de_vaccine_second_delta, de_vaccine_second_quote]
    vaccine_dict['BY'] = [by_vaccine_total, by_vaccine_delta, by_vaccine_quote, by_vaccine_second_total, by_vaccine_second_delta, by_vaccine_second_quote]

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
    data = pd.read_json(url)
 
    data_IN = pd.DataFrame([])
    data_IN = pd.read_json(url_IN, lines=True)

    global de_rki, de_rki_delta

    #try it five times
    for i in range(1,6):                   
        try:
            print (f'try - {i} ...') 
            api_instance = Api(rki_url)
            api_instance.set_session()
            r = api_instance.parse_response()
            last_update_rki = r.meta.lastUpdate
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

    print (f'new cases: {de_rki_delta} ')
    if data.empty:
        print ("API Germany is not responding ...")
        #data = ['no data']
    else:
        #letzte Zeile dropenhttps://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=county%20%3D%20%27SK%20INGOLSTADT%27%20OR%20county%20%3D%20%27LK%20DACHAU%27%20OR%20county%20%3D%20%27LK%20EICHST%C3%84TT%27%20OR%20county%20%3D%20%27LK%20PFAFFENHOFEN%20A.D.ILM%27%20OR%20county%20%3D%20%27LK%20KELHEIM%27&outFields=county,cases7_per_100k,last_update&returnGeometry=false&outSR=4326&f=json
        #data.drop(data.tail(1).index,inplace=True)
        data['datum'] = data['Date'].dt.strftime('%Y-%m-%d')
        data['DeltaConfirmed'] = data['Confirmed'].diff()
        data['mean_last7days'] = data.DeltaConfirmed.rolling(window=rolling_window_avg,min_periods=0).mean()
        data['DeltaPercentage'] = data.DeltaConfirmed.pct_change() * 100
#      data.to_csv (r'export_data.csv', index = False, header=True)
        #pprint (data.tail(days))
    
    global inzidenz_dict
    inzidenz_dict = {}
    ingo = pd.Series(data_IN['features']) 
    data_IN['countyIN'] = ingo.iloc[0][0]['attributes']['county'][3:]
    data_IN['last_updateIN'] = ingo.iloc[0][0]['attributes']['last_update']
    data_IN['cases7_per_100kIN'] = ingo.iloc[0][0]['attributes']['cases7_per_100k']

    data_IN['countyPAF'] = ingo.iloc[0][1]['attributes']['county'][3:]
    data_IN['last_updatePAF'] = ingo.iloc[0][1]['attributes']['last_update']
    data_IN['cases7_per_100kPAF'] = ingo.iloc[0][1]['attributes']['cases7_per_100k']

    data_IN['countyKEH'] = ingo.iloc[0][2]['attributes']['county'][3:]
    data_IN['last_updateKEH'] = ingo.iloc[0][2]['attributes']['last_update']
    data_IN['cases7_per_100kKEH'] = ingo.iloc[0][2]['attributes']['cases7_per_100k']

    data_IN['countyEI'] = ingo.iloc[0][3]['attributes']['county'][3:]
    data_IN['last_updateEI'] = ingo.iloc[0][3]['attributes']['last_update']
    data_IN['cases7_per_100kEI'] = ingo.iloc[0][3]['attributes']['cases7_per_100k']

    data_IN['countyDAH'] = ingo.iloc[0][4]['attributes']['county'][3:]
    data_IN['last_updateDAH'] = ingo.iloc[0][4]['attributes']['last_update']
    data_IN['cases7_per_100kDAH'] = ingo.iloc[0][4]['attributes']['cases7_per_100k']

    inzidenz_dict['IN'] = [str (data_IN['countyIN'][0]), str(data_IN['cases7_per_100kIN'][0])[:5], str(data_IN['last_updateIN'][0])]
    inzidenz_dict['PAF'] = [str (data_IN['countyPAF'][0]), str(data_IN['cases7_per_100kPAF'][0])[:5], str(data_IN['last_updatePAF'][0])]
    inzidenz_dict['KEH'] = [str (data_IN['countyKEH'][0]), str(data_IN['cases7_per_100kKEH'][0])[:5], str(data_IN['last_updateKEH'][0])]
    inzidenz_dict['EI'] = [str (data_IN['countyEI'][0]), str(data_IN['cases7_per_100kEI'][0])[:5], str(data_IN['last_updateEI'][0])]
    inzidenz_dict['DAH'] = [str (data_IN['countyDAH'][0]), str(data_IN['cases7_per_100kDAH'][0])[:5], str(data_IN['last_updateDAH'][0])]

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
            if last_update == '16.01.2021, 00:00 Uhr':
                prev_inzidenz_DAH = 138.8
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
            print ("asf")
            prev_fallzahl_DE = item['DE'][1]
            #prev_fallzahl_BY = item['BY'][1]
            break
    
    return data


def upload_html_b2():    
    b2 = B2()
    bucket = b2.buckets.get('coviddata')

    chart_file = open(chart_filename, 'rb')
    try:
        bucket.files.upload(contents=chart_file, file_name=chart_out_filename)
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


def html(hosp, intensiv, last_update_kh):

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
                elif int (hosp) > 1200:
                    text_color_hosp = "yellow"
                else:
                    text_color_hosp = green
                    text_color_intensiv = green
            except:
                text_color_hosp = green
                text_color_intensiv = green

            new_line_hosp.append(f'''
                       
            <tr>
                <td colspan = 1 style="text-align:left"><img src="https://f003.backblazeb2.com/file/coviddata/hospital.png" class="kh_logo"></td>
                <td colspan = 5 >Neuaufnahmen Krankenhaus (7 Tage)</td>
                <td colspan = 2 style="text-align: left; font-size: 24px; color:{text_color_hosp}">{hosp}</td>
                <td colspan = 4 style="font-size: 10px !important; color:yellow !important;">><br>1.200</td>
            </tr>     
            <tr>
                <td colspan = 1 style="text-align:center"><img src="https://f003.backblazeb2.com/file/coviddata/icu.png" class="kh_logo"></td>
                <td colspan = 5 >Patienten auf Intensivstation</td>                
                <td colspan = 2 style="font-size: 24px; text-align:left; color:{text_color_intensiv}">{intensiv}</td>
                <td colspan = 4 style="font-size: 10px !important; color: red !important">><br>600</td>
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
                                        margin-top: 7px;
                                        margin-bottom: 7px;
                                        margin-left: 20px;
                                        margin-right: 20px;
                                        width:auto;
                                        height:90px; 
                                        border-style: ridge; 
                                        border-color: red;
                                        padding: 10px;
                                        ">
                                    Neuinfektionen gg Vortag DE (RKI)
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
                        </tr>>
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
            add_arrow = '<img src="https://f003.backblazeb2.com/file/coviddata/red_up.png" class="arrow">'
            arrow = "up"
            effect = 'font-effect-fire-animation'
        elif self.inzidenz_vortag < 0:
            add_arrow = '<img src="https://f003.backblazeb2.com/file/coviddata/green_down.png" class="arrow">'
            arrow = "down"
            #color_gn = '#56f86b'
            effect = ''
        elif self.inzidenz_vortag == 0:
            add_arrow = ''
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
    hosp, intensiv, datum = get_hospitalisierung()
    chart_html(hosp, intensiv, datum)
    
    data = retrieve_covid_data()
    retrieve_vaccine_data()
    
    html(hosp[-1], intensiv[-1], datum[-1])
    
    if 'rasp' in hostname:
        #upload only on raspberry
        upload_html_b2() #backblaze bucket
    else:
        pass
    


main()


