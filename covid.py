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

url = 'https://api.covid19api.com/dayone/country/germany'
#url_IN = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&outFields=cases,county,last_update&returnGeometry=false&outSR=4326&f=json'
#url_IN = r'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=county%20%3D%20%27SK%20INGOLSTADT%27&outFields=last_update,county,cases7_per_100k&returnGeometry=false&outSR=4326&f=json'

url_IN = r'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=county%20%3D%20%27SK%20INGOLSTADT%27%20OR%20county%20%3D%20%27LK%20EICHST%C3%84TT%27%20OR%20county%20%3D%20%27LK%20PFAFFENHOFEN%20A.D.ILM%27%20OR%20county%20%3D%20%27LK%20KELHEIM%27&outFields=cases7_per_100k,last_update,county&returnGeometry=false&outSR=4326&f=json'


days = 14
rolling_window_avg = 7

def retrieve_covid_data():
    data = pd.DataFrame([])
    data = pd.read_json(url)
   
    #data_IN = pd.read_json(url_IN)
    #data_IN = StringIO(obj.get()['Body'].read().decode('utf-8')) 
    data_IN = pd.DataFrame([])
    data_IN = pd.read_json(url_IN, lines=True)


    #pprint (list(data.columns.values))

    
    if data.empty:
        print ("API Germany is not responding ...")
        #data = ['no data']
    else:
        #letzte Zeile dropen
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

    inzidenz_dict['IN'] = [str (data_IN['countyIN'][0]), str(data_IN['cases7_per_100kIN'][0])[:5], str(data_IN['last_updateIN'][0])]
    inzidenz_dict['PAF'] = [str (data_IN['countyPAF'][0]), str(data_IN['cases7_per_100kPAF'][0])[:5], str(data_IN['last_updatePAF'][0])]
    inzidenz_dict['KEH'] = [str (data_IN['countyKEH'][0]), str(data_IN['cases7_per_100kKEH'][0])[:5], str(data_IN['last_updateKEH'][0])]
    inzidenz_dict['EI'] = [str (data_IN['countyEI'][0]), str(data_IN['cases7_per_100kEI'][0])[:5], str(data_IN['last_updateEI'][0])]

    last_update = ingo.iloc[0][0]['attributes']['last_update']


    with shelve.open('inzidenz') as db:
        db[last_update]=inzidenz_dict
        db['16.10.2020, 00:00 Uhr']={'IN': ['SK Ingolstadt', '20', '17.10.2020, 00:00 Uhr'], 'PAF': ['LK Pfaffenhofen a.d.Ilm', '15', '17.10.2020, 00:00 Uhr'], 'KEH': ['LK Kelheim', '40', '17.10.2020, 00:00 Uhr'], 'EI': ['LK Eichstätt', '12', '17.10.2020, 00:00 Uhr']}
    
    
    prev_inzidenz = shelve.open('inzidenz')

    for k, item in reversed(sorted(prev_inzidenz.items())):
        if k != last_update:
            prev_inzidenz_IN = item['IN'][1]
            prev_inzidenz_PAF = item['PAF'][1]
            prev_inzidenz_KEH = item['KEH'][1]
            prev_inzidenz_EI = item['EI'][1]
    
    diff_IN  = float(inzidenz_dict['IN'][1])  - float(prev_inzidenz_IN)
    diff_PAF = float(inzidenz_dict['PAF'][1]) - float(prev_inzidenz_PAF)
    diff_KEH = float(inzidenz_dict['KEH'][1]) - float(prev_inzidenz_KEH)
    diff_EI  = float(inzidenz_dict['EI'][1])  - float(prev_inzidenz_EI)
    
    inzidenz_dict['IN'] = inzidenz_dict['IN'] + [diff_IN]
    inzidenz_dict['PAF'] = inzidenz_dict['PAF'] + [diff_PAF]
    inzidenz_dict['KEH'] = inzidenz_dict['KEH'] + [diff_KEH]
    inzidenz_dict['EI'] = inzidenz_dict['EI'] + [diff_EI]

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
            print (label_pct)

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
    cmd1 = 'gsutil cp covid.html gs://'+gs_folder+'/'
    cmd2 = 'gsutil acl ch -u AllUsers:R gs://'+gs_folder+'/covid.html'
    os.system(cmd1)
    os.system(cmd2)


def html():
    add_line=[]
    i = 1

    html_file = 'covid.html'
    htmlfile = open (html_file, 'w')

    for item in html_code.split("\n"):
        if item.find('##COVID_DATA##') > 0:
            for k,v in inzidenz_dict.items():
                add_line.append('<tr>')
                add_line.append(f'<th scope="row">{i}</th>')
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
            item = item.replace('##COVID_DATA##', new_line)
            
       
        htmlfile.write(item)
    htmlfile.close()

class Inzidenz():
    def __init__(self, county, inzidenz, inzidenz_vortag, last_update):
        self.county = county
        self.inzidenz = inzidenz
        self.inzidenz_vortag = inzidenz_vortag
        self.last_update = last_update
    
    def htmlcode(self):
        #print (self.county, self.inzidenz, self.last_update)
        if self.inzidenz_vortag >= 0:
            add_arrow = '<img src="https://storage.googleapis.com/darkshadow-share/green_up1.png" class="arrow">'
        else:
            add_arrow = '<img src="https://storage.googleapis.com/darkshadow-share/red_down1.png" class="arrow">'

        return f'<td>{self.county}</td> <td>{self.inzidenz}</td> <td>{self.inzidenz_vortag} {add_arrow}</td> <td>{self.last_update}</td>'

def main():
    data = retrieve_covid_data()
    plot_data(data)
    upload_plot()
    html()
    upload_html()

html_code = '''
<!doctype html>
<html lang="en">
  <head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!-- Bootstrap CSS -->
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">

<style> 
img.arrow {
  width: auto;
  height: auto;
}

img.plot {
  width: 100%;
  height: auto;
}
</style>

<title>Covid</title>
</head>
<body style="background-color:powderblue;">
    <!-- Optional JavaScript -->
    <!-- jQuery first, then Popper.js, then Bootstrap JS -->
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js" integrity="sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy" crossorigin="anonymous"></script>

  <table class="table table-dark">
  <thead>
    <tr>
      <th scope="col">#</th>
      <th scope="col">Stadt/Landkreis</th>
      <th scope="col">7 Tage Inzidenz pro 100k Einwohner</th>
      <th scope="col">Veränderung gg Vortag</th>
      <th scope="col">last update time</th>
    </tr>
  </thead>
  <tbody>
      ##COVID_DATA##
  </tbody>
</table>
  <img src="https://storage.googleapis.com/darkshadow-share/plot.png" class="plot">
</body>
</html>
'''

main()


