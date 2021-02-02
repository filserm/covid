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

#locale.setlocale(locale.LC_TIME, "de_DE")
#locale.setlocale(locale.LC_ALL, "de_DE.UTF8")

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
#url_IN = r'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=county%20%3D%20%27SK%20INGOLSTADT%27%20OR%20county%20%3D%20%27LK%20EICHST%C3%84TT%27%20OR%20county%20%3D%20%27LK%20PFAFFENHOFEN%20A.D.ILM%27%20OR%20county%20%3D%20%27LK%20KELHEIM%27&outFields=cases7_per_100k,last_update,county&returnGeometry=false&outSR=4326&f=json'
#url_IN = r'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=county%20%3D%20%27SK%20INGOLSTADT%27%20OR%20county%20%3D%20%27LK%20EICHST%C3%84TT%27%20OR%20county%20%3D%20%27LK%20PFAFFENHOFEN%20A.D.ILM%27%20OR%20county%20%3D%20%27LK%20KELHEIM%27&outFields=cases7_per_100k,last_update,county&outSR=4326&f=json'
url_IN = r'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=county%20%3D%20%27SK%20INGOLSTADT%27%20OR%20county%20%3D%20%27LK%20DACHAU%27%20OR%20county%20%3D%20%27LK%20EICHST%C3%84TT%27%20OR%20county%20%3D%20%27LK%20PFAFFENHOFEN%20A.D.ILM%27%20OR%20county%20%3D%20%27LK%20KELHEIM%27&outFields=county,cases7_per_100k,last_update&returnGeometry=false&outSR=4326&f=json'

rki_url = 'https://api.corona-zahlen.org/germany'
#rki_url = 'http://35.209.215.136:8080/germany'
#vaccine_url = 'https://v2.rki.marlon-lueckert.de/vaccinations'
vaccine_url = 'https://api.corona-zahlen.org/vaccinations'

days = 14
rolling_window_avg = 7
now = dt.now() + timedelta(hours=1)

now = now.strftime("%d.%m.%Y, %H:%M Uhr") 

def retrieve_vaccine_data():
    global vaccine_record, last_update_vaccine_formated

    data = s = requests.Session()
    resp = s.get(vaccine_url)
    vaccine = resp.json()
    last_update_vaccine      = vaccine['meta']['lastUpdate']
    last_update_vaccine      = dateutil.parser.parse(last_update_vaccine)
    last_update_vaccine_formated = last_update_vaccine.strftime("%d.%m.%Y, %H:%M Uhr")
    print (last_update_vaccine_formated)

    last_update_vaccine      = str(last_update_vaccine)
    de_vaccine_total = vaccine['data']['vaccinated']
    de_vaccine_delta = vaccine['data']['delta']
    de_vaccine_quote = vaccine['data']['quote']
    by_vaccine_total = vaccine['data']['states']['BY']['vaccinated']
    by_vaccine_delta = vaccine['data']['states']['BY']['delta']
    by_vaccine_quote = vaccine['data']['states']['BY']['quote']
    last_checked = vaccine['data']['states']['BY']['delta']

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

    #print (last_update, de_vaccine_total, de_vaccine_delta, by_vaccine_total, by_vaccine_delta)
    global vaccine_dict
    vaccine_dict = {}
    vaccine_dict['DE'] = [de_vaccine_total, de_vaccine_delta, de_vaccine_quote]
    vaccine_dict['BY'] = [by_vaccine_total, by_vaccine_delta, by_vaccine_quote]

    path = os.path.join(os.path.expanduser("~/covid/"), 'vaccine_db')
    with shelve.open(path) as db:
        db[last_update_vaccine]=vaccine_dict
       
    vaccineDB = shelve.open(path)

    for k, item in sorted(vaccineDB.items(), key=lambda x: (dt.strptime(x[0][:10], '%Y-%m-%d')), reverse=True):
        #print ("Datum", k, "item", item)
        vaccine_record =  item
        print (k, vaccine_record)

    

def retrieve_covid_data():
    data = pd.DataFrame([])
    data = pd.read_json(url)
 
    data_IN = pd.DataFrame([])
    data_IN = pd.read_json(url_IN, lines=True)

    global de_rki, de_rki_delta
    #data_rki = pd.DataFrame([])
    #data_rki = pd.read_json(rki_url, lines=True)
    s = requests.Session()
    resp = s.get(rki_url)
    
    data_rki = resp.json()
    #last_update_rki = data_rki['lastUpdate']
    last_update_rki = data_rki['meta']['lastUpdate']
    de_rki = data_rki['cases']
    de_rki_delta = data_rki['delta']['cases']

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
    data_IN['countyIN'] = ingo.iloc[0][0]['attributes']['county']
    data_IN['last_updateIN'] = ingo.iloc[0][0]['attributes']['last_update']
    data_IN['cases7_per_100kIN'] = ingo.iloc[0][0]['attributes']['cases7_per_100k']

    data_IN['countyPAF'] = ingo.iloc[0][1]['attributes']['county']
    data_IN['last_updatePAF'] = ingo.iloc[0][1]['attributes']['last_update']
    data_IN['cases7_per_100kPAF'] = ingo.iloc[0][1]['attributes']['cases7_per_100k']

    data_IN['countyKEH'] = ingo.iloc[0][2]['attributes']['county']
    data_IN['last_updateKEH'] = ingo.iloc[0][2]['attributes']['last_update']
    data_IN['cases7_per_100kKEH'] = ingo.iloc[0][2]['attributes']['cases7_per_100k']

    data_IN['countyEI'] = ingo.iloc[0][3]['attributes']['county']
    data_IN['last_updateEI'] = ingo.iloc[0][3]['attributes']['last_update']
    data_IN['cases7_per_100kEI'] = ingo.iloc[0][3]['attributes']['cases7_per_100k']

    data_IN['countyDAH'] = ingo.iloc[0][4]['attributes']['county']
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
        print ("Datum", k, "last_update", last_update)
        if k != last_update:
            print ("asf")
            prev_fallzahl_DE = item['DE'][1]
            #prev_fallzahl_BY = item['BY'][1]
            break

    global diff_DE
    diff_DE  = int(float(de_rki)  - float(prev_fallzahl_DE))
    diff_DE = f'{diff_DE:,}'
    diff_DE = diff_DE.replace(',','.')
    
    return data


def plot_data(data):
    f = plt.figure(figsize = (20, 8))
    plt.style.use('dark_background')
    #move_figure(f, 540, 0)

    ''' letzten x Tage ausgeben '''
    latest_x_days = data.tail(days)

    ax = plt.subplot(111)

    text(0.5, 1.10,'Covid19 - confirmed cases (daily delta) Germany',
         horizontalalignment='center',
         verticalalignment='center',
         fontsize=16,
         transform = ax.transAxes,
         color = 'white')

    text(0.5, 1.05,'data source: https://covid19api.com/\nCenter for Systems Science and Engineering (CSSE) at Johns Hopkins University',
         horizontalalignment='center',
         verticalalignment='center',
         fontsize=12,
         transform = ax.transAxes,
         color = 'white')


    #plt.title('Covid19 - confirmed cases Germany')
    plt.bar(latest_x_days['datum'], latest_x_days['DeltaConfirmed'], align='center', label='confirmed cases Germany')
    #plt.bar(latest_x_days_by['datum'], latest_x_days_by['DeltaConfirmed'], align='edge', label='confirmed cases Bavaria',width = 0.3)
    plt.xlabel("Datum",  fontsize = 8)
    ax.tick_params(axis="x", labelsize=8, colors='white')
    ax.tick_params(axis="y", labelsize=8, colors='white')

    #ax.set_xticklabels(latest_x_days['datum'], color='black')
    # Make some labels.

    labels = [int(i) for i in latest_x_days['DeltaConfirmed']]
    rects = ax.patches

    for rect, label in zip(rects, labels):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, height + 5, label,
            ha='center', va='bottom', color='khaki', fontstyle='oblique', fontweight='bold')

    labels_pct = ["%.2f \nPct" % i for i in latest_x_days['DeltaPercentage']]
    for rect, label_pct in zip(rects, labels_pct):
        height = rect.get_height()
        if label_pct.startswith('-'):
            label_pct = '-\n' + label_pct[1:]
        else:
            label_pct = '+\n' + label_pct[0:]
            #print (label_pct)

        ax.text(rect.get_x() + rect.get_width() / 2, height - 400, label_pct,
            ha='center', va='center', color='black', fontstyle='italic', fontsize = 6)


    ax2 = ax.twinx()
    linechart = ax.plot(latest_x_days['datum'], latest_x_days['mean_last'+str(rolling_window_avg)+'days'], color='mediumvioletred', label=str(rolling_window_avg)+' day average Germany')
    ax2.set_yticklabels([])

    loc = plticker.MultipleLocator(base=3.0) # this locator puts ticks at regular intervals
    ax.xaxis.set_major_locator(loc)

    ax.legend(loc="upper left")
    f.savefig('plot.png')

    ax.tick_params(axis="x", labelsize=8, colors='black')
    ax.tick_params(axis="y", labelsize=8, colors='black')

    #plt.show()

def upload_plot():
    gs_folder = "darkshadow-share"
    cmd1 = 'gsutil cp plot.png gs://'+gs_folder+'/'
    cmd2 = 'gsutil acl ch -u AllUsers:R gs://'+gs_folder+'/plot.png'
    os.system(cmd1)
    os.system(cmd2)

def upload_html():
    gs_folder = "darkshadow-share"
    cmd1 = f'gsutil cp {html_filename} gs://{gs_folder}/'
    cmd2 = f'gsutil acl ch -u AllUsers:R gs://{gs_folder}/{html_out_filename}'
    os.system(cmd1)
    os.system(cmd2)


def html():
    
    add_line=[]
    i = 1
    html_template = os.path.join(os.path.expanduser("~/covid/html_template"), 'covid_html_template.html')
    html_template_file = open(html_template, 'r')
    html_code = html_template_file.readlines()

    global html_out_filename, html_filename
    html_out_filename = 'covid.html'
    html_filename = os.path.join(os.path.expanduser("~/covid/html_output"), html_out_filename)
    htmlfile = open (html_filename, 'w')

    for item in html_code:
        if item.find('##COVID_DATA##') > 0:
            for k, v in sorted(inzidenz_dict.items(), key=lambda x: float(x[1][1]), reverse=True):
                add_line.append('<tr>')
                add_line.append(f'<td class="text-align:center;">{i}</td>')
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
            #item = item.replace('##RKI##' , f'<tr><td colspan = 2 class="text-primary">Neuinfektionen DE (RKI):  {diff_DE}</td></tr>')
            
       
        if item.find('##LAST_UPDATE##') > 0:
            item = item.replace('##LAST_UPDATE##' ,f'<tr><td colspan = 6 style="font-size: 10px !important; text-align:right !important; ">letzte Aktualisierung RKI {last_update}</td></tr>')
            #item = item.replace('##LAST_UPDATE##' ,f'<tr><td colspan = 2 class="text-warning">Letzte Aktualisierung:      {last_update}</td></tr>')
        
        if item.find('##VACCINE_HEADER##') >0:
            item = item.replace('##VACCINE_HEADER##' ,f"""
                        
                        <th colspan = 6 class="logo" style="text-align:center"><img src="https://storage.googleapis.com/darkshadow-share/vaccine.svg" class="logo"></th> 
                        <!-- <th colspan = 6 style="text-align:center; font-size: 62px;">{smiley}</th> -->
                        
                        
                        """)

        if item.find('##VACCINE##') >0:
            item = item.replace('##VACCINE##' ,f"""
                        
                        <tr>
                            <td colspan = 2></td>
                            <td class="logo" colspan = 2 style="text-align:center"><img src="https://img.icons8.com/emoji/48/000000/germany-emoji.png" class="flags"> </td>
                            <td colspan = 2 style="text-align:center"><img src="https://img.icons8.com/color/50/000000/bavarian-flag.png" class="flags"> </td>
                        </tr>
                        <tr>
                            <td colspan = 2>Gesamt<p> </p></td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['DE'][0]}<p>{vaccine_dict['DE'][2]}</p></td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['BY'][0]}<p>{vaccine_dict['BY'][2]}</p></td>
                        </tr>
                        <tr> 
                            <td colspan = 2>Diff gg Vortag</td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['DE'][1]} </td>
                            <td colspan = 2 style="text-align:center">{vaccine_dict['BY'][1]} </td>
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
        if self.inzidenz_vortag > 0:
            add_arrow = '<img src="https://storage.googleapis.com/darkshadow-share/red_up.png" class="arrow">'
            arrow = "up"
            effect = 'font-effect-fire-animation'
        elif self.inzidenz_vortag < 0:
            add_arrow = '<img src="https://storage.googleapis.com/darkshadow-share/green_down.png" class="arrow">'
            arrow = "down"
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
        elif arrow == "down":
            return f'<td>{self.county}</td> <td style="color:{color} !important;"><strong>{self.inzidenz_out}</strong></td><td style=text-align:right important!>{self.inzidenz_vortag_out}</td><td colspan=2>{add_arrow}</td>'

def main():
    data = retrieve_covid_data()
    retrieve_vaccine_data()
    #plot_data(data)
    #upload_plot()
    html()
    upload_html()


main()


