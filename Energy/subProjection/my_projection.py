import pandas as pd
from datetime import timedelta

from pandas.core.tools.datetimes import Scalar

from Energy.subTools.weather_data import avg_weather_df

MODEL_COLUMN = ['%sun', '%midsun', '%cloud', 'avg_temp', 'suntime_minutes']
PROJECTION_COLUMNS = ['production_', 'export_', 'import_']

def prepare_dataframes(energy_df, projection):
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
    projection_df.merge(weather_df[['month', '%sun', '%midsun', '%cloud', 'avg_temp', 'suntime_minutes']], how='inner', on="month")
    monthly_energy_df = monthly_energy_df.merge(weather_df[['month', '%sun', '%midsun', '%cloud', 'avg_temp', 'suntime_minutes']], how='inner', on="month")
    return projection_df, monthly_energy_df

from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import Ridge, LinearRegression
from sklearn import metrics
from sklearn.preprocessing import Normalizer, StandardScaler, MinMaxScaler

def create_monthly_projection(energy_df, projection = 6, pdf=None):
    projection_df, monthly_energy_df = prepare_dataframes(energy_df, projection)
    prediction = {}
    
    X = monthly_energy_df[MODEL_COLUMN]
    for projection_col in PROJECTION_COLUMNS:
        
        y = monthly_energy_df[projection_col]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=101)
        scaler = MinMaxScaler()
        scaler.fit(X_train[MODEL_COLUMN[3:]])
        temp = scaler.transform(X_train[MODEL_COLUMN[3:]])
        X_train = X_train[MODEL_COLUMN[:3]]
        X_train[MODEL_COLUMN[3:]] = temp
        temp = scaler.transform(X_test[MODEL_COLUMN[3:]])
        X_test = X_test[MODEL_COLUMN[:3]]
        X_test[MODEL_COLUMN[3:]] = temp
        model = LinearRegression(kernel='linear', C=1, random_state=42)
        scores = cross_val_score(model, X_train, y_train, cv=3, scoring='neg_mean_squared_error')
        model = Ridge(alpha=1, random_state=42)
        scores = cross_val_score(model, X_train, y_train, cv=3, scoring='neg_mean_squared_error')
        temp = scaler.transform(projection_df[MODEL_COLUMN[3:]])
        
        predict = projection_df[MODEL_COLUMN[:3]]
        predict[MODEL_COLUMN[3:]] = temp




    

