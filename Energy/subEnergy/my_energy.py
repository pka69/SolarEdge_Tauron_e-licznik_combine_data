from datetime import date, timedelta, datetime
from abc import ABC, abstractmethod
from numpy import multiply

import pandas as pd
import numpy as np

from ..subGraphs.my_plots import barplot, lineplot, histplot
from ..subGraphs.my_graph_speedo import speedometer, set_of_speedo
from ..subTools.my_pdf import PDF

from Energy import get_debug


def filter_and_group_df(df, filter, group_by, agg='sum', add_avg='' ):
    file_types = {
        'year': [str, "'{}'".format],
        'month': [str, "'{}'".format],
        'week': [str, "'{}'".format],
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
    if add_avg in group_by:
        if type(group_by)==list:
            new_filter = [item for item in group_by if item!=add_avg]
            avg_df = temp_df.groupby(new_filter).mean()
            avg_df = avg_df.reset_index()
            avg_df[add_avg] = 'mean'
        else:
            avg_df = temp_df.groupby(add_avg).mean()
            avg_df = avg_df.reset_index()
        numeric_columns = df.select_dtypes(include=numerics).columns
        temp_df = pd.concat([temp_df, avg_df], reset_index=True)
        for item in numeric_columns:
            filter_avg_df = avg_df[avg_df[new_filter].isin(temp_df[new_filter])]
            # temp_df[item + '_mean'] = temp_df[item] / 
        
        
    return query, filter_name
    
class Energy(ABC):
    '''
    main energy module. 
    Represent all common data for future classes:
    ENERGY_COLUMNS = [production_, export_, import_, direction]
    Unit recalculation: Wh, kWh, MWh
    source_name - source of data

    '''
    ENERGY_COLUMNS = [
        ['production_', 0],
        ['export_',  0],
        ['import_', 0],
        ['direction', 'None']
    ]
    UNITS = {
        'Wh': 1000,
        'kWh': 1,
        'MWh': 0.001
    }
    def __init__(self, 
            source_name = "NoName", # source data name
            direction = 'None', # 
            storage_dir = '/',  # storage place for API data
            output_dir = '/',  # output reports directory
            parent = None,
            export_back = 1,  # back level exported energy
            unit = 'kWh',   # standard energy unit
            day_batch = 5,  # standard API request daytime
            owner = 'Piotr Kalista', 
            location = 'ul. Bluszczowa 4c, Kraków',
            refresh = True,
            kW_cost = 0.65,
            currency = "PLN"
                 ):
        self._energy_df = pd.DataFrame()
        self.source_name = source_name
        self.direction = direction
        self.storage_dir = storage_dir
        self.output_dir = output_dir
        self.parent = parent
        self.export_back = export_back
        self.unit = unit, 
        self.day_batch = day_batch
        self.load_dalta = False
        self.start_date = None
        self.stop_date = None
        self.owner = owner
        self.location = location
        self.debug = get_debug()
        self.refresh = refresh
        self.kW_cost = kW_cost
        self.currency = currency

    def limit_periods(self, period, limit_min, limit_max):
        self._energy_df = self._energy_df[(self._energy_df[period]>=limit_min) & (self._energy_df[period]<=limit_max)]
        self.set_dates()

    def unit_recalc(self, group_by, columns, agg=["sum"]):
        '''
        return aggregated data 
        group_by - grouping list or selected one column
        agg - aggregation type (usually sum)
        '''
        temp_df = self.get_energy.groupby(group_by)[columns].agg(agg)
        temp_max = max([temp_df[item].max() for item in  columns ])
        if temp_max > 10000:
            unit, multiply = 'MWh', 0.001
        elif temp_max < 10:
            unit, multiply = 'Wh', 1000
        else:
            unit, multiply = 'kWh', 1
        return unit, multiply
    
    def get_sum(self, group_by=[], filter_cols=[], filter_values=[], agg='sum'):
        temp_df = self.get_energy
        if filter_cols:
            temp_df = temp_df[temp_df[filter_cols].isin(filter_values)]
        if group_by:
            temp_df = temp_df.groupby(group_by).aggregate(agg)
            temp_df = temp_df.reset_index()
        else:
            temp_df = temp_df.aggregate(agg)
            temp_df['direction'] = self.direction
        return temp_df

    def daily_flash_page(self, 
        filename='daily_flash',
        pdf=None,
    ):
        out_columns = [col for col in self.get_energy.columns if col.endswith("_")]
        by_day_df = self.get_energy[['day'] + out_columns].groupby('day').sum().reset_index()
        stat_df = by_day_df[out_columns].agg(['min', 'max', 'mean']).T.reset_index()
        stat_df = stat_df[stat_df['mean']>0]
        no_of_measures = stat_df['mean'].count()
        plt = set_of_speedo(
            no_of_measures, 
            5, 5 / no_of_measures,  
            stat_df.index.tolist(), 
            stat_df['min'].tolist(),
            stat_df['max'].tolist(), 
            stat_df['mean'].tolist(),
            unit = 'kW', 
            start_angle=-30,
            end_angle=210,
            annotation_fontsize=8,
            annotation_facecolor='gray', 
            annotation_edgecolor="black",
        )
        plt.savefig(self.output_dir + '{}_({%Y%m%d}-{%Y%m%d})'.format(filename, self.start_date, self.stop_date))
        print('report saved: ')
        print(self.output_dir + '{}_({%Y%m%d}-{%Y%m%d})'.format(filename, self.start_date, self.stop_date))

    def basic_barplot(self, 
        group_by='day', 
        columns=['production_', 'import_', 'export_'], 
        colors=[], 
        filename='lineplot', 
        agg="sum", 
        mean=False, 
        ax=None
    ):
        unit, multiply = self.unit_recalc(group_by, columns, agg)
        return barplot(self.get_energy, group_by, columns,colors, agg, unit=unit, multiply=multiply, filename=filename, mean=mean, ax=ax)

    def basic_lineplot(self, 
        group_by='day', 
        columns=['production_', 'import_', 'export_'], 
        colors=[], 
        fill=['production_'], 
        filename='lineplot', 
        agg="sum", 
        filter='', 
        mean=False, 
        ax=None
    ):
        unit, multiply = self.unit_recalc(group_by, columns, agg)
        return lineplot(self.get_energy, group_by, columns, colors, fill, agg, filter=filter, unit=unit, multiply=multiply, filename=filename, mean=mean, ax=ax)
    
    def create_pdf_report(self, 
        group_by, 
        pdf=None,
        filter=None,
        content = ['production', 'consumption', 'flash', 'flow_by_day', ],
        agg='sum',
        add_avg=''
    ):
        if filter or group_by:
            temp_df, filter_name = filter_and_group_df(self.get_energy, filter, group_by, agg, add_avg)
        else:
            temp_df = self.get_energy
            filter_name= ''
        if not pdf:
            pdf = PDF(title=f'energy analyzer. location: {self.location}') 
        
    
    @property
    def direction_list(self):
        return list(set(self.get_energy['direction']))

    @property
    def storage_file(self):
        return '{}{}.{}'.format(self.storage_dir, self.source_name, 'csv')
    
    # @property
    # def energy_df(self):
    #     return self.energy_df()
    
    def load_from_file(self):
        try:
            self.add_df(pd.read_csv(self.storage_file, index_col=0, parse_dates=["date"]))
        except FileNotFoundError as E:
            raise FileNotFoundError("brak pliku '{}' z danymi historycznymi".format(self.storage_file))

    def drop_last_day(self):
        last_day = self._energy_df.day.max()
        self._energy_df = self._energy_df.drop(
                self._energy_df[self._energy_df['day']==last_day].index, axis=0
            )
        return last_day
    
    def save_to_file(self):
        self._energy_df.to_csv(self.storage_file)

    def str_head(self):
        return ''
    
    def __str__(self) -> str:
        output = """
        source data:      {:^23}
        direction:        {:^23}
        dates:            {:%Y/%m/%d} - {:%Y/%m/%d}
        no of timestamp:  {:^23,d}
        export reduction: {:^23.2f}
        no of days:       {:^23,d}
        kW_cost:          {:^23,.2f} {}
         ----------------------------------------------------------------------------------------------------------------------------
        |    import [kWh] |     export [kWh] | production [kWh] |    balance [kWh] | self cons. [kWh] | total cons. [kWh] |
         ----------------------------------------------------------------------------------------------------------------------------
        |{:>16,.2f} | {:>16,.2f} | {:>16,.2f} | {:>16,.2f} | {:>16,.2f} | {:>16,.2f} |
         ----------------------------------------------------------------------------------------------------------------------------
         per day
         --------------------
        |{:>16,.2f} | {:>16,.2f} | {:>16,.2f} | {:>16,.2f} | {:>16,.2f} | {:>16,.2f} |
         ----------------------------------------------------------------------------------------------------------------------------
        """
        saving_output = """
        total savings in currency: {:>16,.2f} {}
        total costs in currency:   {:>16,.2f} {}
        """.format(
            (self.get_energy['self_consumption_'].sum() + self.get_energy['export_'].sum() * self.export_back) * self.kW_cost,
            self.currency,
            self.get_energy['import_'].sum() * self.kW_cost,
            self.currency
        ) if self.kW_cost > 0 else ''

        days = (self.stop_date - self.start_date).days
        return output.format(
            self.source_name,
            self.direction,
            self.start_date,
            self.stop_date,
            self.get_energy.date.count(),
            self.export_back,
            days,
            self.kW_cost, self.currency,
            self.get_energy['import_'].sum(),
            self.get_energy['export_'].sum(),
            self.get_energy['production_'].sum(),
            self.get_energy['balance_'].sum(), 
            self.get_energy['self_consumption_'].sum(),
            self.get_energy['total_consumption_'].sum(), 
            self.get_energy['import_'].sum() / days,
            self.get_energy['export_'].sum() / days,
            self.get_energy['production_'].sum() / days,
            self.get_energy['balance_'].sum() / days,
            self.get_energy['self_consumption_'].sum() / days,
            self.get_energy['total_consumption_'].sum() / days,
        ) + saving_output

    @abstractmethod
    def read_data(self):
        pass

    def refresh__energy_df(self):
        pass

    @property
    def get_energy(self):
        return self._energy_df

    def set_dates(self):
        #
        #   update date_min, date_max based on get_energy_
        #
        self.start_date = self.get_energy.date.min()
        self.stop_date = self.get_energy.date.max()

    def add_df(self, temp_df):
        if isinstance(temp_df, pd.DataFrame):
            self._energy_df = pd.DataFrame()
            self.append_df(temp_df)
        else:
            raise TypeError("it should be an DataFrame object") 

    def append_df(self, temp_df):
        #
        #   adding temp_df to _energy_df
        #
        self.update_df(temp_df)
        self._energy_df = self._energy_df.append(temp_df, ignore_index=True)
        self.set_dates()
        if self.parent:
            self.parent.refresh__energy_df()

    def update_df(self, temp_df):
        #
        #   addnig calculation column balance_, self_consumption_, total_consumption_
        #
        self.add_name_and_direction(temp_df, self.source_name, self.direction)
        self.check_energy_columns(temp_df, self.ENERGY_COLUMNS)
        self.extend_datetime_columns(temp_df)
        temp_df['balance_'] = - (temp_df['import_'] - temp_df['export_'] * self.export_back)
        temp_df['self_consumption_'] = temp_df['production_'] - temp_df['export_']
        temp_df['total_consumption_'] = temp_df['self_consumption_'] + temp_df['import_']

    @staticmethod
    def add_name_and_direction(temp_df, name, direction):
        #
        #   adding standard column source, direction
        #
        if not "source" in temp_df.columns:
            temp_df["source"] = name
        if not "direction" in temp_df.columns:
            temp_df["direction"] = direction

    @staticmethod
    def extend_datetime_columns(temp_df):
        #
        #   adding standard analyzing columns: date, time, year, month, week, hour
        #
        temp_df["day"] = pd.to_datetime(temp_df['date']).dt.date  # .astype(str)
        temp_df['time'] = (
            pd.to_datetime(temp_df['date']).dt.hour * 60 + 
            pd.to_datetime(temp_df['date']).dt.minute
        ) *60
        temp_df['year'] = temp_df['date'].dt.strftime("%Y").astype(str)
        temp_df['month'] = temp_df['date'].dt.strftime("%Y/%m").astype(str)
        temp_df['week'] = temp_df['date'].dt.strftime("%Y/%W").astype(str)
        temp_df['hour'] = temp_df.date.dt.hour
        if any(temp_df['week'].str[-2:]=='00'):
            max_day = temp_df.loc[temp_df['week'].str.endswith('00')]['date'].max()
            max_week = (max_day - pd.Timedelta(days=(max_day.weekday()))).strftime("%Y/%W")
            temp_df.loc[temp_df['week'].str.endswith('00'), 'week'] = max_week

    @staticmethod
    def check_energy_columns(temp_df, columns):
        for col in columns:
            if col[0] not in temp_df.columns:
                temp_df[col[0]] = col[1]
        

class PanelEnergy(Energy):
    def __init__(self, 
                 temp_df, 
                 mean_in_direction, 
                 **kwargs
        ):
        super().__init__(**kwargs)
        if type(self)==PanelEnergy:
            self.source_name = temp_df.iloc[0]['panel']
            self.direction = temp_df.iloc[0]['direction']
            self.direction_mean = mean_in_direction[mean_in_direction['direction']==self.direction]['production_'].max()
            self.all_mean = sum(mean_in_direction['production_'] * mean_in_direction['no_panels']) / mean_in_direction['no_panels'].sum()
            self.append_df(temp_df.drop(['panel'], axis=1))
        
    def read_data(self):
        pass

    def str_head(self):
        head="""         -------------------------------------------------------------------------------------------------
        | panel id       | direction |production [kWh] | prod./day [kWh] |    % vs avg dir |  % vs avg total |  
         -------------------------------------------------------------------------------------------------\n"""
        return head

    def __str__(self) -> str:
        output = """        |{:^16}|{:^10} |{:>16,.2f} |{:>16,.2f} |{:>16,.2%} |{:>16,.2%} |"""
        # if self.parent and self.parent.sub_energy[0]==self:
        #     output = self.head() + output
        days = (self.stop_date - self.start_date).days
        return output.format(
            self.source_name,
            self.direction,
            self.get_energy['production_'].sum(),
            self.get_energy['production_'].sum() / days,
            self.get_energy['production_'].sum() / self.direction_mean,
            self.get_energy['production_'].sum() / self.all_mean,
        )


class CommonEnergy(Energy):
    def __init__(self, sub_energy, **kwargs):
        super().__init__(**kwargs)
        if self.source_name=="NoName":
            self.source_name = 'Common EnergyCollection'
        self.sub_energy = []
        if not type(sub_energy)==list:
            self.append_subenergy(sub_energy)
        else:
            for sub_energy_item in sub_energy:
               self.append_subenergy(sub_energy_item) 
        self.set_dates()

    def read_data(self):
        pass

    def refresh__energy_df(self):
        pass
        self._energy_df = pd.DataFrame()
        for sub_energy in self.sub_energy:
            self.append_df(sub_energy.get_energy)

    def append_subenergy(self, sub_energy):
        if not isinstance(sub_energy, Energy):
            raise TypeError("it should be an Energy object")
            return
        self.append_df(sub_energy.get_energy)
        self.sub_energy.append(sub_energy)
        
    def __str__(self) -> str:
        return self.sub_energy[0].str_head() + '\n'.join([sub.__str__() for sub in self.sub_energy] +[super().__str__()])


