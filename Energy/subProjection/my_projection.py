import pandas as pd
import datetime

from Energy.subTools.weather_data import avg_weather_df


def create_monthly_projection(energy_df, projection = 6, pdf=None):

    weather_df = avg_weather_df()
    monthly_energy_df = energy_df.get_energy.groupby('month').sum().reset_index()
    months = monthly_energy_df.month.values.tolist()
    for month_id in [0, -1]:
        limits = energy_df.get_energy[energy_df.get_energy.month=='2021/08']['day'].agg(['min', 'max']).values.tolist()
        if limits[0].day==1 and (limits[1]+ datetime.timedelta(days=1)).day==1:
            continue
        months.remove(months[month_id])

