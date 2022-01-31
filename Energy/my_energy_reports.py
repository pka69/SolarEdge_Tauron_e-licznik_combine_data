from collections import Counter
import pandas as pd
import numpy as nb


from .LoginData import APIKEY, APIID, TAURON_METER_ID, TAURON_USER_NAME, TAURON_PASS
from Energy import STORAGE_DIR, OUTPUT_DIR, get_debug 
from Energy.subEnergy.my_energy import CommonEnergy, Energy
from Energy.subTools.my_pdf import PDF

from Energy.subEnergy.my_solaredge import MySolarEdge
from Energy.subEnergy.my_tauron import MyTauron, MyAPITauron


MY_SOLAR_DATA = 'my_solar_data.csv'

PERIODS_CONVERTER = {
    'daily': 'day',
    'weekly': 'week',
    'monthly': 'month'
}

def create_energy_reports(
    group='daily', 
    refresh=True, 
    export_back=0.8,
    kWh_cost=0.6,
    limit_periods = None,
):
    # create SorarEdge energy object. USE API SolarEdge
    solar_df = Energy(
        login_data = {'KEY' : APIKEY, "ID" : APIID, 'TIME_UNIT': "HOUR"}, 
        source_name = "SolarEdge",
        export_back = export_back, 
        storage_dir =STORAGE_DIR, 
        output_dir=OUTPUT_DIR,
        refresh=refresh,
        start_date = '2021-08-20',
        kWh_cost = 0
    )
    if limit_periods: solar_df.limit_periods(PERIODS_CONVERTER[group], *limit_periods)
    if get_debug(): print(solar_df)
    # create Tauron energy object. Use API Tauron
    tauron_df = Energy(
        login_data = {"USER_NAME": TAURON_USER_NAME, "PASSWORD": TAURON_PASS, "ID": TAURON_METER_ID}, 
        source_name = "Tauron",
        storage_dir =STORAGE_DIR, 
        output_dir=OUTPUT_DIR,
        refresh=refresh,
        start_date = '2021-08-20',
        kWh_cost = 0
    )
    if limit_periods: tauron_df.limit_periods(PERIODS_CONVERTER[group], *limit_periods)
    if get_debug(): print(tauron_df)
    
    #
    # join objects to one object
    my_energy_df = CommonEnergy(
        [solar_df,tauron_df], 
        storage_dir =STORAGE_DIR, 
        output_dir=OUTPUT_DIR,
        export_back = export_back, 
        kWh_cost = kWh_cost
    )
    if get_debug(): print(my_energy_df)

    pdf = PDF(title="PV installation analyzer. Location: {}".format(my_energy_df.location))

    return my_energy_df, pdf