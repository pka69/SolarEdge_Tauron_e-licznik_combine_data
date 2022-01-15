import pickle

import pandas as pd
from datetime import timedelta

from Energy.subTools.weather_data import avg_weather_df
from Energy.subTools.projection_tools import PROJECTION_COLUMNS, MODEL_NAME
from Energy.subTools.projection_tools import projection_in_graph, projection_refactor, savings_df_report , standarize_data
from Energy import STORAGE_DIR, OUTPUT_DIR, get_debug


def prepare_dataframes(energy_df, projection, pdf = None):
    weather_df = avg_weather_df()
    monthly_energy_df = energy_df.get_energy.groupby('month').sum().reset_index()
    months = monthly_energy_df.month.values.tolist()
    for month_id in [0, -1]:
        limits = energy_df.get_energy[energy_df.get_energy.month==months[month_id]]['day'].agg(['min', 'max']).values.tolist()
        if limits[0].day==1 and (limits[1]+ timedelta(days=1)).day==1:
            continue
        months.remove(months[month_id])
    last_month_start = energy_df.get_energy[energy_df.get_energy.month==months[-1]]['day'].min()
    projection_months = [(last_month_start + pd.DateOffset(months=1 + x)).strftime("%Y/%m") for x in range(projection)]
    monthly_energy_df = monthly_energy_df[monthly_energy_df.month.isin(months)]
    monthly_energy_df['month_str'] = monthly_energy_df.month
    monthly_energy_df.month = monthly_energy_df.month.str[-2:].astype(int)
    projection_df = pd.DataFrame({
        'month': [int(x[-2:]) for x in projection_months],
        'month_str': projection_months
    })
    projection_df = projection_df.merge(weather_df[['month', '%sun', '%midsun', '%cloud', 'avg_temp', 'suntime_minutes']], how='inner', on="month")
    monthly_energy_df = monthly_energy_df.merge(weather_df[['month', '%sun', '%midsun', '%cloud', 'avg_temp', 'suntime_minutes']], how='inner', on="month")
    return projection_df, monthly_energy_df

def create_monthly_projection(energy_df, projection = 6, pdf=None):
    projection_df, monthly_energy_df = prepare_dataframes(energy_df, projection)
    prediction = {}
        
    for idx, projection_col in enumerate(PROJECTION_COLUMNS):
        with open(STORAGE_DIR + MODEL_NAME[idx], 'rb') as file:
            model = pickle.load(file)
            scaler = pickle.load(file)
            MODEL_COLUMN = pickle.load(file)
        sel_projection_df = projection_df[MODEL_COLUMN]
        standardised_projection_df = standarize_data(scaler, sel_projection_df, False, MODEL_COLUMN)
        prediction[projection_col] = model.predict(standardised_projection_df)
        projection_df[projection_col] = prediction[projection_col]

    projection_refactor(projection_df)
    
    if get_debug():
        print(savings_df_report(monthly_energy_df, "historical data summary", kWh_cost = energy_df.kWh_cost, curr = energy_df.currency))
        print(savings_df_report(projection_df, "projection data summary", kWh_cost = energy_df.kWh_cost, curr = energy_df.currency))
    
    if pdf:
        pdf.add_page()
        pdf.set_font('Lato', 'B', 12)
        pdf.cell(0,10, 'Historical data. Period {}-{}'.format(monthly_energy_df['month_str'].min(), monthly_energy_df['month_str'].max()) , 0, 1, 'C')
        
        pdf.set_font('Lato', '', 8)
        savings_msg = savings_df_report(monthly_energy_df, "historical data summary", kWh_cost = energy_df.kWh_cost, curr = energy_df.currency).split('\n')
        
        for msg in savings_msg:
            pdf.cell(100, 6, msg , 0, 1, 'R')
        pdf.set_font('Lato', 'B', 8)
        pdf.cell(0, 10, 'Projection Report. Period {}-{}'.format(projection_df['month_str'].min(), projection_df['month_str'].min()) , 0, 1, 'C')
        pdf.set_font('Lato', '', 8)
        savings_msg = savings_df_report(projection_df, "projection data summary", kWh_cost = energy_df.kWh_cost, curr = energy_df.currency).split('\n')
        for msg in savings_msg:
            pdf.cell(100, 6, msg , 0, 1, 'R')
        filename = OUTPUT_DIR + 'projection graph {}-{}'.format(projection_df['month_str'].min().replace('/', ''), projection_df['month_str'].min().replace('/', ''))
        projection_in_graph(monthly_energy_df, projection_df, filename=filename)
        pdf.image(filename+'.png', None, None, 200, 100, type='PNG')
    return prediction

    

