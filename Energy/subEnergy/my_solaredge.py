from datetime import date, timedelta

import pandas as pd
import numpy as np

from solaredge import solaredge as se

from .my_energy import  Energy

class MySolarEdge(Energy):

    def __init__(self, 
        se_key,  # IPKey to solarEdge Installation 
        se_id,  # installation id 
        time_unit = "HOUR",  # QUARTER_OF_AN_HOUR, HOUR, DAY, WEEK, MONTH, YEAR
        **kwargs
    ):

        super().__init__(source_name = "SolarEdge", **kwargs)
        self.se_key = se_key
        self.se_id = se_id
        self.time_unit = time_unit
        if type(self)==MySolarEdge:
            self.read_data()

    def read_data(self):
        # connect with SolarEdge API
        try:
            s = se.Solaredge(self.se_key)
        except Exception as E:
            print(E)
            return None 
        try:
            dates = s.get_data_period(self.se_id)
            if self.debug:
                print(dates)
        except Exception as E:
            print(E)
            return None  
        start_date = date.fromisoformat(dates["dataPeriod"]["startDate"])  
        end_date = date.fromisoformat(dates["dataPeriod"]["endDate"])
        try:
            self.load_from_file()
            start_date = self.drop_last_day()
            if date.today() - start_date <= timedelta(days=1):
                if self.debug: print(f'{self.source_name}\nTotal produced energy: {self.get_energy.production_.sum():,.2f} wh')
                return
            if not self.refresh: return
        except FileNotFoundError as E:
            print("!!!!!!\n{} - no historical data".format(self.source_name))
        try:
            days = (end_date - start_date).days + 1
            for i in range(0, days, self.day_batch):
                imp_start_date = start_date + timedelta(days=i)
                imp_end_date = min(end_date, imp_start_date + timedelta(days=self.day_batch - 1))
                day_energy = s.get_energy(
                    self.se_id, 
                    imp_start_date.isoformat(), 
                    imp_end_date.isoformat(), 
                    time_unit=self.time_unit 
                )
                temp_df =  temp_df.append( 
                    pd.DataFrame.from_records(day_energy["energy"]["values"]), ignore_index=True
                    ) if i else pd.DataFrame.from_records(day_energy["energy"]["values"])

            temp_df = temp_df.fillna(0)
            temp_df.rename(columns={'value': 'production_'}, inplace = True)
            temp_df['production_'] = temp_df['production_'] * self.UNITS['kWh'] / self.UNITS[day_energy['energy']['unit']]
            temp_df.date = pd.to_datetime(temp_df['date'], format="%Y-%m-%d %H:%M:%S")
            self.append_df(temp_df)
            self.save_to_file()
            if self.debug:
                print(f'{self.source_name}\nTotal produced energy: {self.get_energy.production_.sum()} wh')
        except Exception as E:
            print("!!!!!\n", E)  
        return
