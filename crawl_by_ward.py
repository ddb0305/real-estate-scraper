import asyncio
from asyncio import futures
import csv
import numpy as np
import pandas as pd
import os
import hashlib
import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup


class WC():
    BASE_URL = "https://batdongsan.com.vn"
    ALL = 0
    DAILY = 1
    WEEKLY = 2
    
    def __init__(self, ward):
        self.city_code = ward["city.code"]
        self.district_id = ward["district.id"]
        self.ward_id = ward["id"]
        self.url = ward["url"]
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36')
        self.driver = webdriver.Chrome(options=chrome_options, executable_path="./chromedriver")
        self.delay = 5

    def driver_get(self, url):
        self.driver.get(url)
        WebDriverWait(self.driver, self.delay)
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        return soup

    async def get_pages(self):
        pages = []
        soup = self.driver_get(self.url)

        not_found = soup.find("img", alt="not found")
        if (not_found != None):
            return pages

        try:
            a = soup.find("div", class_="re__pagination-group").findAll("a")
            page_count = int(a[-1]["pid"])
            pages.append(self.url)
            for i in range(2, page_count+1):
                pages.append(self.url+"/p{}".format(i))
        except:
            pages.append(self.url)
        
        return pages

    async def get_all_posts_in_a_page(self, url):
        soup = self.driver_get(url)
        ps = soup.select(".pr-container")
        posts = []

        for p in ps:
            post = {}
            post["prid"] = p["prid"]
            post["url"] = self.BASE_URL + p.select_one(".wrap-plink")["href"]
            posts.append(post)
        
        return posts

    async def get_all_posts(self):
        pages = await self.get_pages()
        tasks = []

        for page in pages:
            task = asyncio.ensure_future(self.get_all_posts_in_a_page(page))
            tasks.append(task)

        res = [item for sublist in await asyncio.gather(*tasks) for item in sublist] 
        return res

    def is_in_interval(self, time: datetime.date, interval):
        today = datetime.date.today()
        if interval == self.DAILY:
            return time == today
        elif interval == self.WEEKLY:
            difference = datetime.date.today() - time
            return 0 <= difference.days <= 6 
        else:
            return False

    async def get_posts_interval(self, interval):
        pages = await self.get_pages()
        posts = [] 
        if not pages:
            return posts

        self.driver.get(self.url)
        print(self.url)
        WebDriverWait(self.driver, self.delay)
        self.driver.find_element_by_id("divSortProduct").click()
        self.driver.find_element_by_xpath('//*[@id="divSortProductOptions"]/ul/li[2]').click()       
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        for page in pages:
            soup = self.driver_get(page)
            ps = soup.select(".pr-container")
            
            post_count = 0
            for p in ps:
                post_time = datetime.datetime.strptime(p.select_one(".product-labeltime .tooltip-time").text, "%d/%m/%Y").date()
                if self.is_in_interval(post_time, interval):                    
                    post = {}
                    post["prid"] = p["prid"]
                    post["url"] = self.BASE_URL + p.select_one(".wrap-plink")["href"]
                    posts.append(post)
                    post_count += 1
            
            if post_count < len(ps):
                break
        return posts

    async def get_details(self, post):
        soup = self.driver_get(post["url"])

        details = {"prid": post["prid"], "url": post["url"]}
        
        scripts = soup.find_all("script")
        for script in scripts:
            try:
                if "FrontEnd.Product.Details.ListingHistory" not in script.string:
                    pass
                else:
                    datas = script.string.split("description:")[0].split("avatarWapSave:")[-1].replace(" ","").replace("\n",'').split(",")[1:]
                    for data in datas:
                        data = data.replace("'", "")
                        key, value = data.split(":")
                        details[key] = value
            except:
                pass
            
            try:
                if "contextValue" not in script.string:
                    pass
                else:
                    datas = script.string.split("});")[0].split("contextValue:")[-1].replace(" ","").replace("\n","")[1:-2].split(",")
                    for data in datas:
                        data = data.replace("'", "")
                        key, value = data.split(":")
                        details[key] = value
            except:
                pass        
            
        return details

    async def crawl_all_in_ward(self, interval):
        if interval == self.ALL:
            posts = await self.get_all_posts()
        else:
            posts = await self.get_posts_interval(interval)
    
        tasks = []

        for post in posts:
            task = asyncio.ensure_future(self.get_details(post))
            tasks.append(task)
        
        res = await asyncio.gather(*tasks)
        self.driver.close()

        return res      

    def write_to_csv(self, datas, directory_path):
        csv_path = directory_path + "/" + self.city_code + "_" + str(self.district_id) + "_" + str(self.ward_id) + ".csv"
        csv_file = open(csv_path, 'w+', newline='', encoding='utf-8')
        c = csv.writer(csv_file)
        
        c.writerow(["pr_id", "url", "value_hash", "price", "price_level", "area", "area_level", "rooms", 
                    "toilets", "direction", "type", "cate", "city", "distr", "ward_id", "street_id", "proj_id"])

        for data in datas:
            try:
                c.writerow(
                    [
                        data["prid"], 
                        data["url"],
                        hashlib.md5(("%s %s %s %s %s %s %s %s %s %s %s %s %s %s" 
                                            %   (data["priceSort"], data["priceLevel"], 
                                                data["areaSort"], data["areaLevel"], data["room"], 
                                                data["toilets"], data["direction"], data["type"], 
                                                data["cate"], data["city"], data["distr"], 
                                                data["wardid"], data["streetid"], 
                                                data["projid"])).encode("utf-8")).hexdigest(),
                        data["priceSort"], 
                        data["priceLevel"], 
                        data["areaSort"], 
                        data["areaLevel"], 
                        data["room"], 
                        data["toilets"], 
                        data["direction"], 
                        data["type"], 
                        data["cate"], 
                        data["city"], 
                        data["distr"], 
                        data["wardid"], 
                        data["streetid"], 
                        data["projid"]]
                )
            except:
                pass  

        csv_file.close()
        print("Created: ", self.city_code + "_" + str(self.district_id) + "_" + str(self.ward_id) + ".csv")



async def main():
    fake_ward =   {
        "city.code": "HN",
        "district.id": 7,
        "name": "Nghĩa Tân",
        "id": 9451,
        "url": "https://batdongsan.com.vn/nha-dat-ban-phuong-nghia-tan-3"
    }

    wc = WC(fake_ward)
    res = await wc.crawl_all_in_ward(wc.WEEKLY)
    wc.write_to_csv(res, os.getcwd())


if __name__ == "__main__": # Crawl a ward and create a csv file in current directory
    # start = time.time()
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(main())       
    loop.run_until_complete(future)    
    # print(time.time() - start) 