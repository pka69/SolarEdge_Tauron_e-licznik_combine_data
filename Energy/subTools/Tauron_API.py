from datetime import datetime, timedelta
import pandas as pd
import requests
from urllib3 import poolmanager
import ssl

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