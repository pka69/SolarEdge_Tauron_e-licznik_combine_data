from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta

import pandas as pd
from solaredge import solaredge as se

from Energy import get_debug
from Energy.subTools.Tauron_API import TauronAPI

SOLAREDGE_TIME_UNITS = ['QUARTER_OF_AN_HOUR', 'HOUR', 'DAY', 'WEEK', 'MONTH', 'YEAR']

class Energy_Interface(ABC):
    name = 'master'
    def __init__(self, login_data, start_date=None, day_batch = 5, UNITS = None):
        super().__init__()
        self.login_data = login_data
        self.start_date = start_date
        self.day_batch = day_batch
        self.units = UNITS
        
    @abstractmethod
    def _init_connection(self):
        pass
    
    @abstractmethod
    def _close_connection(self):
        pass
    
    @abstractmethod
    def get_dataset(self):
        pass
    
    def __enter__(self):
        self._init_connection()
        return self
    
    def __exit__(self, type, value, traceback):
        self._close_connection()
        

class SolarEdge_Interface(Energy_Interface):
    name = 'SolarEdge'
    def _init_connection(self):
        try:
            self.connection = se.Solaredge(self.login_data['KEY'])
            self.time_unit = self.login_data.get('TIME_UNIT', '') if self.login_data.get('TIME_UNIT', '') in SOLAREDGE_TIME_UNITS else 'HOUR'
            self.ID = self.login_data['ID']
            self.debug = get_debug()
        except Exception as E:
            print(E)
        try:
            dates = self.connection.get_data_period(self.ID)
            if self.debug:
                print(dates)
        except Exception as E:
            print(E)
        if not self.start_date: self.start_date = date.fromisoformat(dates["dataPeriod"]["startDate"]) 
        self.end_date = date.fromisoformat(dates["dataPeriod"]["endDate"])
        self.days =  (self.end_date - self.start_date).days + 1 
    
    def get_dataset(self):
        for i in range(0, self.days, self.day_batch):
            imp_start_date = self.start_date + timedelta(days=i)
            imp_end_date = min(self.end_date, imp_start_date + timedelta(days=self.day_batch - 1))
            day_energy = self.connection.get_energy(
                    self.ID, 
                    imp_start_date.isoformat(), 
                    imp_end_date.isoformat(), 
                    time_unit=self.time_unit 
                )
            temp_df = pd.DataFrame.from_records(day_energy["energy"]["values"])
            temp_df = temp_df.fillna(0)
            temp_df.rename(columns={'value': 'production_'}, inplace = True)
            temp_df['production_'] = temp_df['production_'] * self.units['kWh'] / self.units[day_energy['energy']['unit']]
            temp_df.date = pd.to_datetime(temp_df['date'], format="%Y-%m-%d %H:%M:%S")
            yield temp_df
            
    def _close_connection(self):
        self.connection = None


class Tauron_Interface(Energy_Interface):
    name = 'Tauron'
    def _init_connection(self):
        self.connection = TauronAPI(self.login_data['USER_NAME'], self.login_data['PASSWORD'], self.login_data['ID'])
        self.connection.login()
        
        self.end_date = date.today()
        self.days =  (self.end_date - self.start_date).days + 1 
        
    def _close_connection(self):
        self.connection = None
    
    def get_dataset(self):
        for i in range(0, self.days, self.day_batch):
            imp_start_date = self.start_date + timedelta(days=i)
            imp_end_date = min(self.end_date, imp_start_date + timedelta(days=self.day_batch - 1))
            day_energy = self.connection.get_readings(imp_start_date, imp_end_date)
            consumed = dict(self._extract_values_with_timestamps(day_energy.get("chart", [])))
            produced = dict(self._extract_values_with_timestamps(day_energy.get("OZE", [])))
            temp_df = pd.DataFrame( 
                    sorted(
                    (timestamp, float(consumed.get(timestamp)), float(produced.get(timestamp)))
                    for timestamp in set(consumed) | set(produced)
                ), columns=['date', 'import_', 'export_']
            )
            temp_df = temp_df.fillna(0)    
            temp_df.date = temp_df.date - timedelta(hours=1)
            yield temp_df
            
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
            
class SolarEdge_Panel_Interface(Energy_Interface):
    name = 'SolarEdge_Panel'            
            
            
LOGIN_INTERFACE = {i.name: i for i in Energy_Interface.__subclasses__()}