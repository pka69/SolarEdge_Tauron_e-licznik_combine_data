from datetime import date, datetime, timedelta


import pandas as pd

from .my_energy import  Energy
from Energy import STORAGE_DIR, OUTPUT_DIR
from Energy.subTools.Tauron_API import TauronAPI

        
class MyTauron(Energy):
    def __init__(self, 
        files,  # filelist with tauron data
        **kwargs
    ) -> None:
        super().__init__(source_name = "Tauron", **kwargs)
        self.files = files
        if type(self)==MyTauron:
            self.read_data()

    def read_data(self):
        temp_df = pd.DataFrame()
        for file in self.files:
            if temp_df.empty:
                temp_df = pd.read_csv(file, parse_dates=['Data, godzina'], sep=";", decimal=',', encoding='cp1250')
            else:
                temp_df = temp_df.append(pd.read_csv(file, parse_dates=['Data, godzina'], sep=";", decimal=',', encoding='cp1250'), ignore_index=True) 
        temp_df.drop(['Unnamed: 3'], axis=1, inplace=True)
        temp_df.rename(
            columns = {
                'Data, godzina': 'date',
                'Pobór energii [kWh]': 'import_',
                'Oddanie [kWh]': 'export_'
            }, inplace = True
        )
        temp_df.date = temp_df.date  - timedelta(hours=1)
        temp_df['production_'] = 0
        temp_df["day"] = pd.to_datetime(temp_df['date']).dt.date  # .astype(str)
        self.add_df(temp_df)
        if self.debug:
            print(f'{self.source_name}\nTotal import energy: {self.get_energy.import_.sum():,.2f} {self.unit}\nTotal export energy: {self.get_energy.export_.sum():,.2f} {self.unit}')
        
class MyAPITauron(MyTauron):
    def __init__(self, 
                 username, 
                 password, 
                 meter_id, 
                 start_date = '2021-08-20', 
                 **kwargs
        ) -> None:
        super().__init__('', **kwargs)
        self.username = username
        self.password = password
        self.meter_id = meter_id
        self.start_installation_date = date.fromisoformat(start_date)
        if type(self)==MyAPITauron:
            self.read_data()
        
    def read_data(self):
        start_date = self.start_installation_date
        end_date = date.today()
        try:
            self.load_from_file()
            start_date = self.drop_last_day()
            if not self.refresh:
                if self.debug:
                    print(
                        f'{self.source_name}\nTotal import energy:' +  
                        f'{self.get_energy.import_.sum():,.2f} {self.unit}\nTotal export energy: ' + 
                        f'{self.get_energy.export_.sum():,.2f} {self.unit}'
                    )
                return
        except FileNotFoundError as E:
            print("!!!!!!\n{} - no historical data".format(self.source_name))
        s = TauronAPI(self.username, self.password, self.meter_id)
        s.login()
        try:
            days = (end_date - start_date).days + 1
            for i in range(0, days, self.day_batch):
                date_srt = start_date + timedelta(days=i)
                end_date_srt = min(end_date, date_srt + timedelta(days=self.day_batch - 1))
                day_energy = s.get_readings(date_srt, end_date_srt)
                temp_df =  temp_df.append(day_energy, ignore_index=True
                    ) if i else day_energy
            temp_df = temp_df.fillna(0)    
            temp_df.date = temp_df.date - timedelta(hours=1)
            self.append_df(temp_df)
            self.save_to_file()
        except Exception as E:
            print("!!!!!\n", E)  
        finally:
            del(s)
        if self.debug:
            print(f'{self.source_name}\nTotal import energy: {self.get_energy.import_.sum():,.2f} wh\nTotal export energy: {self.get_energy.export_.sum():,.2f} wh')
        return