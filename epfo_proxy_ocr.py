from selenium import webdriver
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import pandas as pd
import requests
import easyocr
import json
import re
import cv2
import pytesseract
import numpy as np
import os
import base64
import io
import time
import threading
import calendar
import random
import valid_proxies
from PIL import Image
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.chrome.options import Options

month_names = []

reader = easyocr.Reader(['en'], gpu=True)

def bypass_captcha_easyocr(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.copyMakeBorder(gray, 10, 10, 10, 10, cv2.BORDER_REPLICATE)
    
    # Adaptive thresholding
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    letter_image_regions = sorted([cv2.boundingRect(contour) for contour in contours], key=lambda x: x[0])

    predictions = []

    for x, y, w, h in letter_image_regions:
        if w * h < 100:
            continue

        if y-2 < 0 or x-2 < 0 or (y + h + 2) > gray.shape[0] or (x + w + 2) > gray.shape[1]:
            continue

        letter_image = gray[y-2:y+h+2, x-2:x+w+2]
        
        if letter_image.size == 0:
            continue
        
        letter_image_resized = cv2.resize(letter_image, (50, 50))
        
        result = reader.readtext(letter_image_resized, paragraph=False, low_text=0.3, contrast_ths=0.5)
        
        if result and len(result) > 0:
            predictions.append(result[0][1].strip().upper())

    final_text = ''.join(predictions)
    return final_text


def wait_for_element(driver, locator, timeout=10):
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.presence_of_element_located(locator))
        # print("Loading indicator found")
    except TimeoutException:
        # print("Loading indicator not found within the initial wait time")
        return True

def wait_for_element_to_disappear(driver, locator, timeout=10):
    try:
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.invisibility_of_element_located(locator))
        # print("Loading indicator disappeared")
        return False
    except TimeoutException:
        # print("Loading indicator did not disappear within the maximum wait time")
        return True


# Function to check if a proxy is working
def is_proxy_working(proxy):
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}",
    }
    try:
        response = requests.get("http://www.example.com", proxies=proxies, timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False
    
curr_valid_proxies = [proxy for proxy in valid_proxies.ipArray if is_proxy_working(proxy)]

URL = "https://unifiedportal-emp.epfindia.gov.in/publicPortal/no-auth/misReport/home/loadEstSearchHome"
wrong_count = 0

def epfo_scrapping(company_name, company_code, name):
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    # If no working proxies, raise an error
    if not curr_valid_proxies:
        raise Exception("No valid proxies available")
    chrome_options.add_argument(f"--proxy-server={random.choice(curr_valid_proxies)}")

    # proxy add
    # PROXY = random.choice(valid_proxies.ipArray)
    # webdriver.DesiredCapabilities.CHROME['proxy'] = {
    #     "httpProxy": PROXY,
    #     "ftpProxy": PROXY,
    #     "sslProxy": PROXY,
    #     "proxyType": "MANUAL",
    # }
    # webdriver.DesiredCapabilities.CHROME['acceptSslCerts']=True

    oneTime=True
    global wrong_count
    flag=0
    response = {
        "matches" : {
            "name": "",
            "epf_history": {}
        },
        "pf_filing_details" : [],
        "establishment_info": {
            "establishment_id": "",
            "establishment_name": "",
            "date_of_setup": "",
            "ownership_type": ""
        }
    }
    response["matches"]["name"] = name

    for j in range(0, 26):
        for i in range(0, 26):
            driver = webdriver.Chrome(options=chrome_options)
            # ip check
            driver.get("https://httpbin.org/ip")
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            body = soup.find('body')
            time.sleep(2)
            print(body.getText())
            try:
                driver.get(URL)
                flag=0
                usernameEntry = driver.find_element(By.XPATH, '//*[@id="estName"]')
                usernameEntry.send_keys(company_name)
                codeNumber = driver.find_element(By.XPATH, '//*[@id="estCode"]')
                codeNumber.send_keys(company_code)
                while True:
                    image_element = driver.find_element(By.ID, "capImg")
                    image_screenshot_base64 = image_element.screenshot_as_base64
                    image_data = base64.b64decode(image_screenshot_base64)
                    image = Image.open(io.BytesIO(image_data))
                    image.save(f"ss{threading.current_thread().name}.png")
                    image = cv2.imread(f"ss{threading.current_thread().name}.png")
                    captcha_text = bypass_captcha_easyocr(image)
                    # print(captcha_text)
                    captchaEntry = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                    captchaEntry.send_keys(captcha_text)
                    time.sleep(2)
                    
                    try:
                        element2 = driver.find_element(By.XPATH, '//*[@id="searchEmployer"]')
                        element2.click()
                    except UnexpectedAlertPresentException as e:
                        alert = driver.switch_to.alert
                        alert.accept()
                        driver.refresh()
                        time.sleep(1)
                        break

                    # print("Search button clicked")
                    time.sleep(1)

                    wait_for_element(driver, (By.XPATH, '/html/body/div[4]'), timeout=1)
                    if (wait_for_element_to_disappear(driver, (By.XPATH, '/html/body/div[4]'), timeout=30)):
                        continue

                    # print("I am here")
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    try:
                        if soup.find_all('div', class_='establishment-list')[0].find_all('div')[-1].get_text() == 'Please enter valid captcha.':
                            wrong_count += 1
                            print("Wrong captcha", wrong_count)
                            continue
                        else:
                            flag=1 
                            pass
                    except:
                        pass
                    # print("All good")

                    try:
                        element3 = driver.find_element(By.XPATH, '//*[@title="Click to view establishment details."]')
                        element3.click()
                        time.sleep(2)
                    except:
                        driver.refresh()
                        time.sleep(1)
                        flag=0
                        break

                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')

                    tableBody = soup.find('div', id='tablecontainer5').find_all('div')[-1].find('table').find('tbody')
                    tableRow0 = tableBody.find_all('tr')[0]
                    establishment_name = tableRow0.find_all('td')[1].get_text()
                    establishment_id = tableRow0.find_all('td')[3].get_text()
                    tableRow4 = tableBody.find_all('tr')[4]
                    ownership_type = tableRow4.find_all('td')[1].get_text()
                    date_of_setup = tableRow4.find_all('td')[3].get_text()

                    response['establishment_info']['establishment_name'] = establishment_name
                    response['establishment_info']['establishment_id'] = establishment_id
                    response['establishment_info']['date_of_setup'] = date_of_setup
                    response['establishment_info']['ownership_type'] = ownership_type
                
                    onclickText = soup.find('div', id='tablecontainer3').find('a')
                    result = re.search(r"\('(.*?)'\)", onclickText['onclick'])
                    part = result.group(1)
                    
                    # print(part)
                    newURL = "https://unifiedportal-emp.epfindia.gov.in" + part
                    driver.get(newURL)

                    i=0
                    my_set = set()
                    month_dictionary = dict()
                    prevCount=0
                    while True:
                        element5 = driver.find_element(By.XPATH, '//*[@data-dt-idx = "6"]')
                        element5.click()

                        page_source = driver.page_source
                        soup = BeautifulSoup(page_source, 'html.parser')
                        tbody = soup.find('tbody')
                        count_trs = len(tbody.find_all('tr'))

                        if oneTime == True:
                            last_row = soup.find_all('tr')[-1]
                            last_mon = last_row.find_all('td')[-3].get_text()
                            date_obj = datetime.strptime(last_mon, '%b-%y')
        
                            previous_month = date_obj - relativedelta(months=1)
                            two_months_ago = date_obj - relativedelta(months=2)
                            
                            prev_month_str = previous_month.strftime('%b-%y').upper()
                            two_months_ago_str = two_months_ago.strftime('%b-%y').upper()

                            month_names = [last_mon, prev_month_str, two_months_ago_str]
                            oneTime=False

                        if (i == count_trs):
                            i=0
                            prevCount+=1

                        temp = prevCount
                        while (temp > 0) :
                            temp -= 1
                            prevElement = driver.find_element(By.XPATH, '//*[@class = "paginate_button previous"]')
                            prevElement.click()
                            # time.sleep(1)

                        flag1 = False

                        while True:
                            page_source = driver.page_source
                            soup = BeautifulSoup(page_source, 'html.parser')
                            tbody = soup.find('tbody')
                            row = soup.find_all('tr')[-(i+1)]
                            month = row.find_all('td')[-3].get_text()
                            date_of_credit = row.find_all('td')[1].get_text()
                            date_obj = datetime.strptime(date_of_credit, '%d-%b-%Y %H:%M:%S')
                            formatted_month = date_obj.strftime('%b-%y').upper()
                            count_rows = len(tbody.find_all('tr'))
                            if (formatted_month == month_names[2]):
                                flag1 = True
                                break
                            if month in month_names:
                                my_set.add(month)
                                break
                            else:
                                i+=1
                            if (i == count_rows):
                                i=0
                                prevCount += 1
                                prevElement = driver.find_element(By.XPATH, '//*[@class = "paginate_button previous"]')
                                prevElement.click()

                        if (flag1 == True):
                            break

                        total_amount = row.find_all('td')[-4].get_text().strip()
                        total_amount = total_amount.replace(',', '')
                        employees_count = row.find_all('td')[-2].find('a').get_text()
                        response["pf_filing_details"].append({
                            "total_amount": int(total_amount),
                            "employees_count": int(employees_count),
                            "wage_month": month
                        })

                        element6 = driver.find_element(By.XPATH, f'(//*[@title="Click to view member details."])[last()-{i}]')
                        element6.click()
                        time.sleep(2)

                        wait_for_element(driver, (By.XPATH, '/html/body/div[4]'), timeout=1)
                        if (wait_for_element_to_disappear(driver, (By.XPATH, '/html/body/div[4]'), timeout=300)):
                            continue

                        element7 = driver.find_element(By.XPATH, '(//*[@aria-controls="example"])[2]')
                        element7.send_keys(name)
                        # time.sleep(1)

                        try:
                            driver.find_element(By.XPATH, '//*[@class= "dataTables_empty"]')
                            result = "false"
                        except NoSuchElementException:
                            result = "true"

                        if (month in month_dictionary):
                            if (month_dictionary[month] == 'false'):
                                month_dictionary[month] = result
                        else:
                            month_dictionary[month] = result
                        driver.refresh()
                        i+=1

                    for key, value in month_dictionary.items():
                        response["matches"]["epf_history"][key] = value

                    aggregated_data = defaultdict(lambda: {"total_amount": 0, "employees_count": 0})
                    for entry in response["pf_filing_details"]:
                        mon = entry["wage_month"]
                        aggregated_data[mon]["total_amount"] += entry["total_amount"]
                        aggregated_data[mon]["employees_count"] += entry["employees_count"]
                    response["pf_filing_details"] = []
                    for wage_month, data in aggregated_data.items():
                        response['pf_filing_details'].append({
                            "total_amount": data["total_amount"],
                            "employees_count": data["employees_count"],
                            "wage_month": wage_month
                        })

                    json_response = json.dumps(response, indent=2)
                    print(json_response)
                    driver.delete_all_cookies()
                    driver.close()
                    break
                if flag==1:
                    break
            except:
                flag=0
                driver.refresh()
                time.sleep(1)
                break
        if flag==1:
            break

thread1 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ABHIJEET KUMAR SINGH"))
thread2 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "ROHIT VERMA"))
thread3 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "BENAKA N"))
thread4 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ADIL DASTGIR SHAIKH"))
thread5 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "ABHIJEET KUMAR SINGH"))
thread6 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "CHANDINI S GOWDA"))
thread7 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "MD ADNANUDDIN"))
thread8 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "ABHIJEET KUMAR SINGH"))
thread9 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "CHAITALI UMESH BHAGWAT"))
thread10 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "BINDUSHREE B N"))
thread11 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "AAKARSHAN CHAUHAN"))
thread12 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "ABDUL KAYES N"))
thread13 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "ABHISHEK ASHOK KUMAR SINGH"))
thread17 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "AAYUSH KUMAR"))
thread18 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "UMMER FAROOK KASSIM"))
thread19 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "TUSHAR DHANAI"))
thread20 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "VARSHA SHETTY"))
thread21 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ABHIJEET KUMAR SINGH"))
thread22 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ROHIT VERMA"))
thread23 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "BENAKA N"))
# thread14 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "VUDUGULA ANJU GOUD"))
# thread15 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "ZARANA GAURAV CHINTAL"))
# thread16 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "ABHISHEK ASHOK KUMAR SINGH"))
# thread24 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ADIL DASTGIR SHAIKH"))
# thread25 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "ABHIJEET KUMAR SINGH"))
# thread26 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "CHANDINI S GOWDA"))
# thread27 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "MD ADNANUDDIN"))
# thread28 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "ABHIJEET KUMAR SINGH"))
# thread29 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "CHAITALI UMESH BHAGWAT"))
# thread30 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "BINDUSHREE B N"))
# thread31 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "AAKARSHAN CHAUHAN"))
# thread32 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "ABDUL KAYES N"))
# thread33 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "ABHISHEK ASHOK KUMAR SINGH"))
# thread34 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "VUDUGULA ANJU GOUD"))
# thread35 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "ZARANA GAURAV CHINTAL"))
# thread36 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "ABHISHEK ASHOK KUMAR SINGH"))
# thread37 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "AAYUSH KUMAR"))
# thread38 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "UMMER FAROOK KASSIM"))
# thread39 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "TUSHAR DHANAI"))
# thread40 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "VARSHA SHETTY"))
# thread41 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ABHIJEET KUMAR SINGH"))
# thread42 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ROHIT VERMA"))
# thread43 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "BENAKA N"))
# thread44 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ADIL DASTGIR SHAIKH"))
# thread45 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "ABHIJEET KUMAR SINGH"))
# thread46 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "CHANDINI S GOWDA"))
# thread47 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "MD ADNANUDDIN"))
# thread48 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "ABHIJEET KUMAR SINGH"))
# thread49 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "CHAITALI UMESH BHAGWAT"))
# thread50 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "BINDUSHREE B N"))
# thread51 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "AAKARSHAN CHAUHAN"))
# thread52 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "ABDUL KAYES N"))
# thread53 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "ABHISHEK ASHOK KUMAR SINGH"))
# thread54 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "VUDUGULA ANJU GOUD"))
# thread55 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "ZARANA GAURAV CHINTAL"))
# thread56 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "ABHISHEK ASHOK KUMAR SINGH"))
# thread57 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "AAYUSH KUMAR"))
# thread58 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "UMMER FAROOK KASSIM"))
# thread59 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "TUSHAR DHANAI"))
# thread60 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "VARSHA SHETTY"))

thread1.start()
# thread2.start()
# thread3.start()
# thread4.start()
# thread5.start()
# thread6.start()
# thread7.start()
# thread8.start()
# thread9.start()
# thread10.start()
# thread11.start()
# thread12.start()
# thread13.start()
# thread17.start()
# thread18.start()
# thread19.start()
# thread20.start()
# thread21.start()
# thread22.start()
# thread23.start()
# thread14.start()
# thread15.start()
# thread16.start()
# thread24.start()
# thread25.start()
# thread26.start()
# thread27.start()
# thread28.start()
# thread29.start()
# thread30.start()
# thread31.start()
# thread32.start()
# thread33.start()
# thread34.start()
# thread35.start()
# thread36.start()
# thread37.start()
# thread38.start()
# thread39.start()
# thread40.start()
# thread41.start()
# thread42.start()
# thread43.start()
# thread44.start()
# thread45.start()
# thread46.start()
# thread47.start()
# thread48.start()
# thread49.start()
# thread50.start()
# thread51.start()
# thread52.start()
# thread53.start()
# thread54.start()
# thread55.start()
# thread56.start()
# thread57.start()
# thread58.start()
# thread59.start()
# thread60.start()

thread1.join()
# thread2.join()
# thread3.join()
# thread4.join()
# thread5.join()
# thread6.join()
# thread7.join()
# thread8.join()
# thread9.join()
# thread10.join()
# thread11.join()
# thread12.join()
# thread13.join()
# thread17.join()
# thread18.join()
# thread19.join()
# thread20.join()
# thread21.join()
# thread22.join()
# thread23.join()
# thread14.join()
# thread15.join()
# thread16.join()
# thread24.join()
# thread25.join()
# thread26.join()
# thread27.join()
# thread28.join()
# thread29.join()
# thread30.join()
# thread31.join()
# thread32.join()
# thread33.join()
# thread34.join()
# thread35.join()
# thread36.join()
# thread37.join()
# thread38.join()
# thread39.join()
# thread40.join()
# thread41.join()
# thread42.join()
# thread43.join()
# thread44.join()
# thread45.join()
# thread46.join()
# thread47.join()
# thread48.join()
# thread49.join()
# thread50.join()
# thread51.join()
# thread52.join()
# thread53.join()
# thread54.join()
# thread55.join()
# thread56.join()
# thread57.join()
# thread58.join()
# thread59.join()
# thread60.join()
