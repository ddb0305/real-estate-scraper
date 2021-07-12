import os
import asyncio
import ast

from crawl_by_ward import WC
from datetime import date

class Routine():
    ALL = (0, "all")
    DAILY = (1, "daily")
    WEEKLY = (2, "weekly")

    def __init__(self, wards):
        self.wards = wards  # list of wards
        self.data_directory = os.getcwd() + "/bds-raw-datas"

        if not os.path.exists(self.data_directory):
            os.makedirs(self.data_directory)

    async def crawl_all(self, interval):
        today = date.today()
        directory  = self.data_directory + "/" + interval[1] + "/" + str(today.year) + "-" + str(today.month) + "-" + str(today.day)

        if not os.path.exists(directory):
            os.makedirs(directory)
        
        for ward in self.wards:
            wc = WC(ward)
            res = await wc.crawl_all_in_ward(interval[0])
            wc.write_to_csv(res, directory)

# XXX: Crawling everything would take about 48 hours for 35 GB worth of datas
if __name__ == "__main__":
    test_wards = []
    with open("test_wards.json", "r") as f:
        test_wards = ast.literal_eval(f.read())

    r = Routine(test_wards)
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(r.crawl_all(r.DAILY))   
    loop.run_until_complete(future)    
    