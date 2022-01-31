from datetime import datetime
import pandas as pd

def filter_and_group_df(df, filter, group_by, agg='sum', add_avg='' ):
    file_types = {
        'year': [str, "'{}'".format],
        'month': [str, "'{}'".format],
        'week': [str, "'{}'".format],
        'hour': [np.int64, int],
        'direction': [str, "'{}'".format],
        'date': [datetime, datetime.fromisoformat],
        'production_': [np.float64, float],
        'export_': [np.float64, float],
        'import_': [np.float64, float],
        'balance_': [np.float64, float],
        'production_per_panel': [np.float64, float],
        'self_consumption_': [np.float64, float],
        'total_consumption_': [np.float64, float],
        'source_': [str, "'{}'".format],   
    }
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']

    query = ''
    filter_name = ''
    if filter:
        try:
            for key, item in filter.items():
                filter_name += item['logic_between'] if item.get('logic_between', '') else '' + key 
                if file_types[item['Column']][0]!=type(item['Value']) or file_types[item['Column']][0]==str:
                    item['Value'] = file_types[item['Column']][1](item['Value'])
                query += (' ' + item['logic_between'] if item.get('logic_between', '') else '') + ' ' + str(item['Column']) + item['Condition'] + str(item['Value'])
            query = query.strip().replace("  ", " ")
            temp_df = df.query(query)
        except ValueError as E:
            raise ValueError('EnergyClass filter construction not valid: ' & E)
    else:
        temp_df = df
    if group_by:
        temp_df = temp_df.groupby(group_by).agg(agg)
        temp_df = temp_df.reset_index()
    if add_avg and (add_avg in group_by):
        if type(group_by)==list:
            new_filter = [item for item in group_by if item!=add_avg]
            avg_df = temp_df.groupby(new_filter).mean()
            avg_df = avg_df.reset_index()
        else:
            avg_df = temp_df.groupby(add_avg).mean()
            avg_df = avg_df.reset_index()
        avg_df[add_avg] = 'mean'
        numeric_columns = df.select_dtypes(include=numerics).columns
        temp_df = pd.concat([temp_df, avg_df], reset_index=True)
        for item in numeric_columns:
            filter_avg_df = avg_df[avg_df[new_filter].isin(temp_df[new_filter])]
            # temp_df[item + '_mean'] = temp_df[item] / 
        
        
    return temp_df, filter_name
    