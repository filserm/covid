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

url = 'https://api.covid19api.com/dayone/country/germany'
url_IN = 'https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&outFields=cases,county,last_update&returnGeometry=false&outSR=4326&f=json'
url_by = 'https://covid19-germany.appspot.com/timeseries/DE-BY/cases'

#url_new_cases = 'https://api.covid19api.com/dayone/country/germany/status/confirmed/live'
#url_all_data = 'https://api.coronatab.app/places/closest'

days = 30
rolling_window_avg = 20

def retrieve_covid_data():
    data = pd.DataFrame([])
    data = pd.read_json(url)
    #data_by = pd.read_json(url_by)
    #data_IN = pd.read_json(url_IN)
    '''
    retrieve_messages = requests.get(url_IN)
    data_IN = retrieve_messages.json()

    loaded_json = json.dumps(data_IN)
    for x in data_IN:
           if re.search('Ingolstadt', str(data_IN[x])):
               data_all = data_IN[x]

    for y, z in enumerate(data_all):
        print (y, z)

    pprint (data_all[222])
    exit()
    '''

    retrieve_messages = requests.get(url_by)
    data_by = retrieve_messages.json()

    data_all_by = []
    for x in data_by:
        #pprint (data_by[x])
        data_all_by.extend([data_by[x] for x in data_by])

    cols = ['datum', 'ConfirmedCases']
    lst = []
    for item in data_all_by[0]:
        for k,v in item.items():
            lst.append([k, v])
    data_by = pd.DataFrame(lst, columns=cols)
    data_by['datum'] = [ts[0:10] for ts in data_by['datum']]
    data_by['DeltaConfirmed'] = data_by['ConfirmedCases'].diff()
    data_by['mean_last20days'] = data_by.DeltaConfirmed.rolling(window=rolling_window_avg,min_periods=0).mean()
    data_by['DeltaPercentage'] = data_by.DeltaConfirmed.pct_change() * 100
    data_by.to_csv (r'export_data_by.csv', index = False, header=True)
    #pprint (data_by)

    #pprint (list(data.columns.values))

    if data.empty:
        print ("API Germany is not responding ...")
        #data = ['no data']
    else:
        #letzte Zeile dropen
        data.drop(data.tail(1).index,inplace=True)
        data['datum'] = data['Date'].dt.strftime('%Y-%m-%d')
        data['DeltaConfirmed'] = data['Confirmed'].diff()
        data['mean_last20days'] = data.DeltaConfirmed.rolling(window=rolling_window_avg,min_periods=0).mean()
        data['DeltaPercentage'] = data.DeltaConfirmed.pct_change() * 100
        data.to_csv (r'export_data.csv', index = False, header=True)
        pprint (data.tail(days))


    return data, data_by


def plot_data(data, data_by):
    f = plt.figure(figsize = (20, 8))
    plt.style.use('dark_background')
    #move_figure(f, 540, 0)

    ''' letzten x Tage ausgeben '''
    latest_x_days = data.tail(days)
    #latest_x_days_by = data_by.tail(days)

    ''' für 2 Timeseries ...
    end_datum = data.datum.tail(1)
    end_datum_by = data_by.datum.tail(1)

    end_datum = end_datum.to_list()
    end_datum = dt.strptime(end_datum[0], '%Y-%m-%d')

    end_datum_by = end_datum_by.to_list()
    end_datum_by = dt.strptime(end_datum_by[0], '%Y-%m-%d')

    day = timedelta(days=days)
    start_datum = end_datum -day
    start_datum  = start_datum.strftime("%Y-%m-%d")
    end_datum  = end_datum.strftime("%Y-%m-%d")
    end_datum_by  = end_datum_by.strftime("%Y-%m-%d")
    lst_end_datum = [end_datum, end_datum_by]
    end_datum = min(lst_end_datum)
    print (end_datum)


    print (start_datum, end_datum)
    mask = (data['datum'] > start_datum) & (data['datum'] <= end_datum)
    latest_x_days = data.loc[mask]
    mask_by = (data_by['datum'] > start_datum) & (data_by['datum'] <= end_datum)
    latest_x_days_by = data_by.loc[mask_by]
    print (latest_x_days)
    print (latest_x_days_by)
    '''


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
    plt.bar(latest_x_days['datum'], latest_x_days['DeltaConfirmed'], align='edge', label='confirmed cases Germany',width = -0.7)
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

    '''
    #### DATEN BAYERN
    labels_by = [int(i) for i in latest_x_days_by['DeltaConfirmed']]
    rects = ax.patches

    for rect, label in zip(rects, labels_by):
        height = rect.get_height() -100
        ax.text(rect.get_x() + rect.get_width() / 1, height + 5, label,
            ha='center', va='bottom', color='khaki', fontstyle='oblique', fontweight='bold')

    labels_pct = ["%.2f \nPct" % i for i in latest_x_days_by['DeltaPercentage']]
    for rect, label_pct in zip(rects, labels_pct):
        height = rect.get_height()
        if label_pct.startswith('-'):
            label_pct = '-\n' + label_pct[1:]
        else:
            label_pct = '+\n' + label_pct[0:]
            print (label_pct)

        ax.text(rect.get_x() + rect.get_width() / 1.8, height - 100, label_pct,
            ha='center', va='center', color='black', fontstyle='italic', fontsize = 8)
    '''

    ax2 = ax.twinx()
    linechart = ax.plot(latest_x_days['datum'], latest_x_days['mean_last'+str(rolling_window_avg)+'days'], color='mediumvioletred', label='20 day average Germany')
    #linechart = ax.plot(latest_x_days_by['datum'], latest_x_days_by['mean_last'+str(rolling_window_avg)+'days'], color='blue', label='20 day average Bavaria')
    ax2.set_yticklabels([])

    loc = plticker.MultipleLocator(base=3.0) # this locator puts ticks at regular intervals
    ax.xaxis.set_major_locator(loc)

    #ax.grid(True, linestyle='-.')
    ax.legend(loc="upper right")
    #plt.tight_layout()
    #f.savefig('plot.png', dpi=f.dpi)
    f.savefig('plot.png')

    ax.tick_params(axis="x", labelsize=8, colors='black')
    ax.tick_params(axis="y", labelsize=8, colors='black')

    #plt.show()

def upload_plot():
    gs_folder = "darkshadow-share"
    cmd = [f"gsutil cp plot.png gs://{gs_folder}/",
           f"gsutil acl ch -u AllUsers:R gs://{gs_folder}/plot.png"
          ]
    for commands in cmd:
        os.system(commands)


def main():
    data, data_by = retrieve_covid_data()
    plot_data(data, data_by)
    upload_plot()

main()
