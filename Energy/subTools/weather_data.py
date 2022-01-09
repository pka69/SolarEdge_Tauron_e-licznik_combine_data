import pandas as pd
from datetime import time
import os
from Energy import STORAGE_DIR
from Energy.subTools.tools import file_list
SUN_WEATHER_DATA_FILE = 'weather_data.xlsx'
SUN_WEATHER_PREPARED_DATA_FILE = 'weather_data.csv'

def prepare_sun_data():
    time_parser = lambda x: pd.to_datetime(x, format="%H:%M")
    
    sun_df = pd.read_excel(
        'other/' + SUN_WEATHER_DATA_FILE, 
        sheet_name='sunrice_sunset', 
        parse_dates=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24],
        date_parser=time_parser,
    )
    for month in range(1,13):
        for zone in ['_up', '_down']:
            column = '{}{}'.format(month, zone)
            sun_df[column] = sun_df[column].dt.hour*60 + sun_df[column].dt.minute  
    return sun_df

def avg_weather_df():
    get_time_str = lambda x: '{}:{:02d}'.format(int(x // 60), int(x % 60))
    weather_df = pd.read_excel(
        'other/' + SUN_WEATHER_DATA_FILE, 
        sheet_name='months_weather', 
    )
    avg_sun_df = prepare_sun_data().mean()
    weather_df['sunrice_minutes'] = weather_df['month'].apply(lambda x: avg_sun_df['{}_up'.format(x)])
    weather_df['sunset_minutes'] = weather_df['month'].apply(lambda x: avg_sun_df['{}_down'.format(x)])
    weather_df['suntime_minutes'] = weather_df['sunset_minutes'] - weather_df['sunrice_minutes']
    weather_df['sunrice'] = pd.to_datetime(weather_df['sunrice_minutes'].apply(get_time_str), format="%H:%M")
    weather_df['sunset'] = pd.to_datetime(weather_df['sunset_minutes'].apply(get_time_str), format="%H:%M")
    weather_df['suntime'] = pd.to_datetime(weather_df['suntime_minutes'].apply(get_time_str), format="%H:%M")
    return weather_df

if __name__=="__main__":
    avg_weather_df()