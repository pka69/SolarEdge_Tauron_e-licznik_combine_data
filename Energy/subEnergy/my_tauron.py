from datetime import date, datetime, timedelta
import requests
from urllib3 import poolmanager
import ssl

import pandas as pd
import numpy as np

from solaredge import solaredge as se

from .my_energy import  Energy
from Energy import STORAGE_DIR, OUTPUT_DIR

class TLSAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=False):
        """Create and initialize the urllib3 PoolManager."""
        ctx = ssl.create_default_context()
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        self.poolmanager = poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_version=ssl.PROTOCOL_TLS,
            ssl_context=ctx,
        )
        
class Session(requests.Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mount("https://", TLSAdapter())

class TauronAPI:
    SERVICE_URL = "https://elicznik.tauron-dystrybucja.pl"
    LOGIN_URL = "https://logowanie.tauron-dystrybucja.pl/login"
    CHART_URL = "https://elicznik.tauron-dystrybucja.pl/index/charts"
    
    def __init__(self, username, password, meter_id):
        self.username = username
        self.password = password
        self.meter_id = meter_id
        
    def login(self):
        self.session = Session()
        self.session.get(self.LOGIN_URL)
        self.session.post(
            self.LOGIN_URL,
            data={
                "username": self.username,
                "password": self.password,
                "service": self.SERVICE_URL,
            },
        )
        
    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_raw_readings(self, start_date, end_date):
        return self.session.post(
            self.CHART_URL,
            data={
                "dane[smartNr]": self.meter_id, 
                "dane[chartDay]": end_date.strftime("%d.%m.%Y"),
                "dane[paramType]": "csv",
                "dane[trybCSV]": "godzin",
                "dane[startDay]": start_date.strftime("%d.%m.%Y"),
                "dane[endDay]": end_date.strftime("%d.%m.%Y"),
                "dane[checkOZE]": "on",
            },
        ).json()
    
    @staticmethod
    def _extract_values_with_timestamps(data):
        for element in data:
            date = element.get("Date")
            hour = int(element.get("Hour"))
            value = float(element.get("EC"))
            # TODO: There's also an "Extra" field, which seems to be set to be set to "T" only for the one extra hour
            # when switching from CEST to CET (e.g. 3 AM on 2021-10-31)
            timestamp = datetime.strptime(date, "%Y-%m-%d")
            timestamp += timedelta(hours=hour)
            value = element.get("EC")
            yield timestamp, value

    def get_readings(self, start_date, end_date):
        data = self.get_raw_readings(start_date, end_date)
        data = data.get("dane", {})
        consumed = dict(self._extract_values_with_timestamps(data.get("chart", [])))
        produced = dict(self._extract_values_with_timestamps(data.get("OZE", [])))
        return pd.DataFrame( 
                sorted(
                (timestamp, float(consumed.get(timestamp)), float(produced.get(timestamp)))
                for timestamp in set(consumed) | set(produced)
            ), columns=['date', 'import_', 'export_']
        )
        
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
            print(f'{self.source_name}\nTotal import energy: {self.get_energy.import_.sum():,.2f} wh\nTotal export energy: {self.get_energy.export_.sum():,.2f} wh')
        
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
                        f'{self.get_energy.import_.sum():,.2f} wh\nTotal export energy: ' + 
                        f'{self.get_energy.export_.sum():,.2f} wh'
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