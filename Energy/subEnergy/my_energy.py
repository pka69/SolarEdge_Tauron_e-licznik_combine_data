from datetime import date, timedelta, datetime
from abc import ABC, abstractmethod

from numpy import multiply
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from ..subGraphs.my_plots import barplot, lineplot, set_of_speedo, swarmplot, simple_data_preparation
from ..subTools.my_pdf import PDF
from .my_intrerfaces import LOGIN_INTERFACE
from Energy import get_debug

# LOGIN_INTERFACE = {
#     'SolarEdge' : SolarEdge_Interface,
#     'Tauron' : "interface",
# }

class Energy(ABC):
    '''
    main energy module. 
    Represent all common data for future classes:
    ENERGY_COLUMNS = [production_, export_, import_, direction]
    Unit recalculation: Wh, kWh, MWh
    source_name - source of data
    direction - used foe panels - panel direction (West, East, South, North)
    '''
    ENERGY_COLUMNS = [
        ['production_', 0],
        ['export_',  0],
        ['import_', 0],
        ['direction', 'None']
    ] # basic energy columns
    
    UNITS = {
        'Wh': 1000,
        'kWh': 1,
        'MWh': 0.001
    } #energy units and muliply vs standard energy column (kWh)
    
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
            kWh_cost = 0.65,
            currency = "PLN",
            login_data = {},
            start_date = None, 
            stop_date = None,
                 ):
        self._energy_df = pd.DataFrame()
        self.source_name = source_name      
        self.direction = direction
        self.storage_dir = storage_dir
        self.output_dir = output_dir
        self.parent = parent
        self.export_back = export_back
        self.unit = unit
        self.day_batch = day_batch
        self.load_data = False  # do wykasowania
        self.start_date = start_date
        self.stop_date = stop_date
        self.owner = owner
        self.location = location
        self.debug = get_debug()
        self.refresh = refresh
        self.kWh_cost = kWh_cost
        self.currency = currency
        self.login_data = login_data
        self.interface = LOGIN_INTERFACE[self.source_name] if (self.source_name and self.source_name!="NoName") else None
        # if type(self)==Energy:
        self.read_data()

    def limit_periods(self, period, limit_min, limit_max):
        # trim data to selected periods (min - max)
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
        set_of_speedo(stat_df, self.output_dir + '{}_speedo_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date))
        if self.debug:
            print('saved png file: ', end="")
            print(self.output_dir + '{}_speedo_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date))
        if pdf:
            pdf.add_page()
            pdf.set_font('Lato', 'B', 12)
            pdf.cell(0, 10, ' Flash Report. Period {:%Y/%m/%d}-{:%Y/%m/%d}. export back: {:.1%}, cost {:.2f} {}/{} '.format(
                self.start_date, self.stop_date, self.export_back, self.kWh_cost, self.currency, self.unit) , 1, 1, 'C')
            
            pdf.set_font('Lato', 'B', 8)
            pdf.cell(0, 5, 'average of main statistic (daily). Range between daily min - daily max', 0, 1, 'C')
            pdf.image(self.output_dir + '{}_speedo_({:%Y%m%d}-{:%Y%m%d}).png'.format(filename, self.start_date, self.stop_date),None, None, 200, 50, type='PNG')
            pdf.cell(0, 5, ' '.join(self.saving_output().split('\n')) , 0, 1, 'C')
        group_by='hour' 
        columns=['production_', 'export_']
        colors=[] 
        filename_g=self.output_dir + '{}_byHour_1_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
        agg="max" 
        fill=[]
        fill_between = {
            'self_consumption': ['production_', 'export_'],
            'mean_self_consumption': ['mean_production_', 'mean_export_'],
        }
        filter = ''
        unit=self.unit
        title = 'Max Production and Export energy by hour a day'
        mean=True 
        ax=None
        figsize=(6, 3)
        lineplot(self.get_energy, group_by, columns, 
            colors=colors, fill=fill, agg=agg, 
            filter=filter, unit=unit, fill_between=fill_between,
            filename=filename_g, mean=mean, title = title, 
            figsize=figsize, ax=ax
        )
        if self.debug:
            print('saved png file: ', end="")
            print(filename_g)
        if pdf:
            pdf.image(filename_g + '.png',50, None, 120, 60, type='PNG') 
        columns=['total_consumption_', 'import_']
        title = 'max Import and Total Consumption energy by hour a day'
        fill_between = ''
        filename_g=self.output_dir + '{}_byHour_2_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
        lineplot(self.get_energy, group_by, columns, 
            colors=colors, fill=fill, agg=agg, 
            filter=filter, unit=unit,  
            filename=filename_g, mean=mean, title = title, 
            figsize=figsize, ax=ax
        )
        if self.debug:
            print('saved png file: ', end="")
            print(filename_g)
        if pdf:
            pdf.image(filename_g + '.png',50, None, 120, 60, type='PNG') 
        filename_g=self.output_dir + '{}_swarmplot_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)   
        group_by='day' 
        self.basic_swarmplot(
            group_by, out_columns,
            agg='sum',
            filename=filename_g,
            figsize=figsize, 
            title="daily distribution by category"
        )
        if self.debug:
            print('saved png file: ', end="")
            print(filename_g)
        if pdf:
            pdf.image(filename_g + '.png',50, None, 120, 60, type='PNG') 
            
    def group_report_pages(self, 
        filename='group_report',
        group_by='day',
        table_include=False,
        pdf=None,
    ):
        out_columns = [col for col in self.get_energy.columns if col.endswith("_") and (self.get_energy[col].min()!=0 or self.get_energy[col].max()!=0 )]
        group_by = group_by.split("(")[0]
        unit, multiply = self.unit_recalc(group_by, out_columns, 'sum')
        if table_include:
            table_df = simple_data_preparation(self.get_energy, group_by=group_by, series_to_plot=out_columns,unit=self.unit)[0]
            table_df_avg = table_df.mean()
            table_df_avg = {col: table_df_avg[col] for col in out_columns}
            table_df_avg[group_by] = 'mean'
            table_df = table_df.append(table_df_avg, ignore_index=True)
            for col in out_columns:
                table_df[col + "_(% avg)"] = table_df[col] / table_df_avg[col]
            temp_col = [group_by] + sorted(table_df.columns.tolist()[1:])
            table_df = table_df[temp_col]
            filename_g = self.output_dir + '{}_table_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
            if pdf:
                
                for row in range(len(table_df.index)):
                    if row % 46 == 0:
                        pdf.add_page()
                        pdf.set_font('Lato', 'B', 14)
                        pdf.cell(0,10, 'Summary table by {}, period: {:%Y/%m/%d}-{:%Y/%m/%d}{}'.format(
                            group_by, self.start_date, self.stop_date, ' (cont.)' if row > 0 else '') , 0, 1, 'C')
                        pdf.set_font('Roboto', '', 6)
                        pdf.cell(45)
                        pdf.set_fill_color(125, 125, 125)
                        for idx, col in enumerate(temp_col[1:]):
                            if idx % 2 == 0:
                                pdf.cell(22, 5, col.strip().replace("_"," ") , 1, 0, 'C', 1)
                        pdf.cell(0,5,' ', 0,1)
                        pdf.cell(5)
                        pdf.cell(40,5, group_by , 1, 0, 'C', True)
                        for idx, col in enumerate(temp_col[1:]):
                            pdf.cell(12, 5, unit , 1, 0, 'C', 1) if idx % 2 == 0 else pdf.cell(10, 5, "% of avg" , 1, 0, 'C', 1)
                        pdf.cell(0,5,' ', 0, 1)
                        fill_cell = 0
                        
                    pdf.cell(5)
                    if str(table_df.iloc[row][group_by]) == "mean": fill_cell = 1
                    pdf.cell(40,5, str(table_df.iloc[row][group_by]) , 1, 0, 'C', fill_cell)
                    for idx, col in enumerate(temp_col[1:]):
                        if idx % 2 == 0:
                            pdf.cell(12,5, '{:,.2f}'.format(multiply * table_df.iloc[row][col]).replace(',', ' ') , 1, 0, 'C', fill_cell)
                        else:
                            pdf.cell(10,5, '{:,.1%}'.format(table_df.iloc[row][col]).replace(',', ' ') , 1, 0, 'C', fill_cell)
                    pdf.cell(0,5,' ', 0,1)
                pdf.set_font('Roboto', 'B', 6)
                pdf.cell(5)
                pdf.cell(40,5, 'Summary' , 1, 0, 'C', 0)
                for idx, col in enumerate(temp_col[1:]):
                    pdf.cell(12, 5, '{:,.2f}'.format(multiply * table_df[table_df[group_by]!='mean'][col].sum()).replace(',', ' ') , 1, 0, 'C', 0) if idx % 2 == 0 else pdf.cell(10, 5, "" , 1, 0, 'C', 0)
            table_df.to_excel(filename_g+'.xlsx')
            if self.debug:
                print('saved xlsx report: ', end="")
                print(filename_g+'.xlsx')
        filename_g = self.output_dir + '{}_b1_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
        self.basic_barplot( 
            group_by=group_by, 
            columns=['production_', 'self_consumption_'], 
            colors=['green', 'blue'], 
            filename=filename_g, 
            agg="sum", 
            mean=False, 
            ax=None
        )
        filename_g = self.output_dir + '{}_b2_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
        self.basic_barplot( 
            group_by=group_by, 
            columns=['total_consumption_', 'import_'], 
            colors=['gray', 'red'], 
            filename=filename_g, 
            agg="sum", 
            mean=False, 
            ax=None
        )
        filename_g = self.output_dir + '{}_b3_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
        self.basic_barplot( 
            group_by=group_by, 
            columns=['balance_', 'production_'], 
            colors=['orange', 'green'], 
            filename=filename_g, 
            agg="sum", 
            mean=False, 
            ax=None
        )
        if pdf:
            pdf.add_page()
            pdf.set_font('Lato', 'B', 12)
            pdf.cell(0, 10, ' simply bar reports. Period {:%Y/%m/%d}-{:%Y/%m/%d}. export back: {:.1%}, cost {:.2f} {}/{} '.format(
                self.start_date, self.stop_date, self.export_back, self.kWh_cost, self.currency, self.unit) , 0, 1, 'C')
            pdf.set_font('Lato', 'B', 8)
            pdf.cell(0, 5, 'summary production / self consumption energy (by {}).'.format(group_by), 0, 1, 'C')
            filename_g = self.output_dir + '{}_b1_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
            pdf.image(filename_g + '.png', None, None, 150, 75, type='PNG')
            pdf.cell(0, 5, 'summary total consumption / import energy (by {}).'.format(group_by), 0, 1, 'C')
            filename_g = self.output_dir + '{}_b2_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
            pdf.image(filename_g + '.png', None, None, 150, 75, type='PNG')
            pdf.cell(0, 5, 'summary energy balance / PV production (by {}).'.format(group_by), 0, 1, 'C')
            filename_g = self.output_dir + '{}_b3_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
            pdf.image(filename_g + '.png', None, None, 150, 75, type='PNG')
        if self.debug:
                print('saved png files: ')
                print("   " + self.output_dir + '{}_b1_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date))
                print("   " + self.output_dir + '{}_b2_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date))
                print("   " + self.output_dir + '{}_b3_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date))
        filename_g = self.output_dir + '{}_l1_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
        filter_day = {
            'od 8 rano': {
                'Column': 'hour',
                'Condition': '>=',
                "Value": 8,
            },
            'do 20 wieczorem': {
                'Column': 'hour',
                'Condition': '<',
                "Value": 20,
                'logic_between': "and"
            },
        }
        filter_night = {
            'od 8 rano': {
                'Column': 'hour',
                'Condition': '<',
                "Value": 8,
            },
            'do 20 wieczorem': {
                'Column': 'hour',
                'Condition': '>=',
                "Value": 20,
                'logic_between': "and"
            },
        }
        self.basic_lineplot(
            group_by=group_by, 
            columns=['production_', 'import_', 'export_', ], 
            colors=[], 
            fill=['production_'], 
            filename=filename_g, 
            agg="sum", 
            mean=False, 
            ax=None
        )
        filename_g = self.output_dir + '{}_l2_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
        self.basic_lineplot(
            group_by=group_by, 
            columns=['total_consumption_', 'production_', 'self_consumption_'], 
            colors=[], 
            fill=['production_'], 
            filename=filename_g, 
            agg="sum", 
            mean=False, 
            ax=None
        )
        filename_g = self.output_dir + '{}_sw1_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
        self.basic_swarmplot(
            group_by, 
            out_columns,
            agg='sum',
            filename=filename_g,
            dotsize=5
        )
        if pdf:
            pdf.add_page()
            pdf.set_font('Lato', 'B', 12)
            pdf.cell(0, 10, ' simply line reports. Period {:%Y/%m/%d}-{:%Y/%m/%d}. export back: {:.1%}, cost {:.2f} {}/{} '.format(
                self.start_date, self.stop_date, self.export_back, self.kWh_cost, self.currency, self.unit) , 0, 1, 'C')
            pdf.set_font('Lato', 'B', 8)
            pdf.cell(0, 5, 'production, import, export energy (by {}).'.format(group_by), 0, 1, 'C')
            filename_g = self.output_dir + '{}_l1_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
            pdf.image(filename_g + '.png', None, None, 150, 75, type='PNG')
            pdf.cell(0, 5, 'total consumption, production, self consumption energy (by {}).'.format(group_by), 0, 1, 'C')
            filename_g = self.output_dir + '{}_l2_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
            pdf.image(filename_g + '.png', None, None, 150, 75, type='PNG')
            pdf.cell(0, 5, 'distribution per category (by {}).'.format(group_by), 0, 1, 'C')
            filename_g = self.output_dir + '{}_sw1_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date)
            pdf.image(filename_g + '.png', None, None, 150, 75, type='PNG')
        if self.debug:
                print('saved png files: ')
                print("   " + self.output_dir + '{}_l1_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date))
                print("   " + self.output_dir + '{}_l2_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date))
                print("   " + self.output_dir + '{}_sw3_({:%Y%m%d}-{:%Y%m%d})'.format(filename, self.start_date, self.stop_date))
                
    def basic_barplot(self, 
        group_by='day', 
        columns=['production_', 'import_', 'export_'], 
        agg="sum", 
        colors=[], 
        filename='', 
        mean=False, 
        ax=None,
        **kwargs
    ):
        unit, multiply = self.unit_recalc(group_by, columns, agg)
        return barplot(self.get_energy, group_by, columns,colors, agg, unit=unit, 
                       multiply=multiply, filename=filename, mean=mean, ax=ax, **kwargs)

    def basic_swarmplot(self, 
        group_by='day', 
        columns=['production_', 'import_', 'export_'], 
        agg="sum", 
        colors=[], 
        filename='', 
        mean=False, 
        ax=None,
        dotsize=2,
        **kwargs
    ):
        unit, multiply = self.unit_recalc(group_by, columns, agg)
        return swarmplot(self.get_energy, group_by, columns,colors=colors, agg=agg, 
                         unit=unit, multiply=multiply, filename=filename, mean=mean, dotsize=dotsize, ax=ax, **kwargs)

    def basic_lineplot(self, 
        group_by='day', 
        columns=['production_', 'import_', 'export_'], 
        colors=[], 
        fill=['production_'], 
        filename='', 
        agg="sum", 
        filter='', 
        mean=False, 
        ax=None,
        **kwargs
    ):
        unit, multiply = self.unit_recalc(group_by, columns, agg)
        
        return lineplot(self.get_energy, group_by, columns, colors=colors, 
                        fill=fill, agg=agg, filter=filter, unit=unit, multiply=multiply, filename=filename, mean=mean, ax=ax, **kwargs)
    
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
    
    def saving_output(self):
        output = """
        total savings in currency: {:>16,.2f} {}
        total costs in currency:   {:>16,.2f} {}
        """.format(
            (self.get_energy['self_consumption_'].sum() + self.get_energy['export_'].sum() * self.export_back) * self.kWh_cost,
            self.currency,
            self.get_energy['import_'].sum() * self.kWh_cost,
            self.currency
        ) if self.kWh_cost > 0 else ''
        return output
    
    def __str__(self) -> str:
        output = """
        source data:      {:^23}
        direction:        {:^23}
        dates:            {:%Y/%m/%d} - {:%Y/%m/%d}
        no of timestamp:  {:^23,d}
        export reduction: {:^23.2f}
        no of days:       {:^23,d}
        kWh_cost:          {:^23,.2f} {}
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

        days = (self.stop_date - self.start_date).days
        return output.format(
            self.source_name,
            self.direction,
            self.start_date,
            self.stop_date,
            self.get_energy.date.count(),
            self.export_back,
            days,
            self.kWh_cost, self.currency,
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
        ) + self.saving_output()

    
    def read_data(self):
        start_date = self.start_date
        try:
            self.load_from_file()
            start_date = self.drop_last_day()
        except FileNotFoundError as E:
            print("!!!!!!\n{} - no historical data".format(self.source_name))
        if not self.refresh:
            self.debug_import_msg()
            return
        with self.interface(self.login_data, start_date, self.day_batch, self.UNITS) as connection:
            for temp_df in connection.get_dataset():
                self.append_df(temp_df)
        self.save_to_file()
        self.debug_import_msg()

    def refresh__energy_df(self):
        pass
    
    def debug_import_msg(self):
        if not self.debug: return
        output = {col[0].strip('_').replace('_', " "): self.get_energy[col[0]].sum() for col in self.ENERGY_COLUMNS if col[0].endswith("_") and self.get_energy[col[0]].sum()>0}
        output_str = "\n".join([f'Total energy {key:15} - {value:,.2f} {self.unit}:' for key, value in output.items()])
        print(f'Source: {self.source_name}\n---------------------------------------\n' + output_str) 

    @property
    def get_energy(self):
        return self._energy_df

    def set_dates(self, d_min=None, d_max=None):
        #
        #   update date_min, date_max based on get_energy_
        #
        if d_min:
            self.start_date = d_min
            to_drop = self._energy_df[self._energy_df['day'] < d_min].index.tolist()
            self._energy_df.drop(to_drop, inplace=True)
        else:
            self.start_date = self.get_energy.date.min()
        if d_max:
            self.stop_date = d_min
            to_drop = self._energy_df[self._energy_df['day'] > d_max].index.tolist()
            self._energy_df.drop(to_drop, inplace=True)
        else:
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
        self.temp_subenergy = sub_energy
        super().__init__(**kwargs)
        if self.source_name=="NoName":
            self.source_name = 'Common EnergyCollection'

    def read_data(self):
        self.sub_energy = []
        if not type(self.temp_subenergy)==list:
            self.append_subenergy(self.temp_subenergy)
            d_min, d_max = self.temp_subenergy.get_energy.day.min(), self.temp_subenergy.get_energy.day.max()
        else:
            d_min, d_max = self.temp_subenergy[0].get_energy.day.min(), self.temp_subenergy[0].get_energy.day.max()
            for sub_energy_item in self.temp_subenergy:
               self.append_subenergy(sub_energy_item) 
               if sub_energy_item.get_energy.day.min() > d_min:
                   d_min = sub_energy_item.get_energy.day.min()
               if sub_energy_item.get_energy.day.max() < d_max:
                   d_max = sub_energy_item.get_energy.day.max()    
        self.set_dates(d_min, d_max)
        self.temp_subenergy = None

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


