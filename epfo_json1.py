from selenium import webdriver
from datetime import datetime
import pandas as pd
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
from PIL import Image
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument("--headless") 

current_month = datetime.now().month
starting_month = current_month - 1
month_names = [calendar.month_name[(starting_month - i) % 12 or 12] for i in range(5)]



def bypass_captcha(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray = cv2.copyMakeBorder(gray, 10, 10, 10, 10, cv2.BORDER_REPLICATE)

    thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV, cv2.THRESH_OTSU)[1]

    contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    letter_image_regions = []

    for contour in contours:
        (x, y, w, h) = cv2.boundingRect(contour)
        letter_image_regions.append((x, y, w, h))

    letter_image_regions = sorted(letter_image_regions, key=lambda x: x[0])
    output = cv2.merge([gray] * 3)
    aa=0
    predictions = []
    pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
    for letter_bounding_box in letter_image_regions:
        aa+=1
        x, y, w, h = letter_bounding_box
        letter_image = gray[y - 2:y + h + 2, x - 2:x + w + 2]
        letter_image = cv2.resize(letter_image, (30,30))
        img = Image.fromarray(letter_image).convert("RGB")
        pixdata = img.load()
        threshold=100
        for y in range(img.size[1]):
            for x in range(img.size[0]):
                if (pixdata[x, y][0] > threshold) \
                        and (pixdata[x, y][1] > threshold) \
                        and (pixdata[x, y][2] > threshold):

                    pixdata[x, y] = (255, 255, 255, 255)
                else:
                    pixdata[x, y] = (0, 0, 0, 255)
        custom_config = r'-l eng  --psm 10 -c tessedit_char_whitelist="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" '
        answer = pytesseract.image_to_string(img, config=custom_config)
        predictions.append(answer.replace('\n','').upper())
        img.save(str(aa)+'.png')
    predictions = ''.join(predictions)
    return predictions

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

URL = "https://unifiedportal-emp.epfindia.gov.in/publicPortal/no-auth/misReport/home/loadEstSearchHome"
flag=0

def epfo_scrapping(company_name, company_code, name):
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
            driver = webdriver.Chrome()
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
                captcha_text = bypass_captcha(image)
                # print(captcha_text)
                captchaEntry = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                captchaEntry.send_keys(captcha_text)
                time.sleep(2)
                
                try:
                    element2 = driver.find_element(By.XPATH, '//*[@id="searchEmployer"]')
                    element2.click()
                except:
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
                        continue
                    else:
                        flag=1 
                        pass
                except:
                    pass
                # print("All good")
                element3 = driver.find_element(By.XPATH, '//*[@title="Click to view establishment details."]')
                element3.click()
                time.sleep(2)

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
                prevCount=0
                while True:
                    element5 = driver.find_element(By.XPATH, '//*[@data-dt-idx = "6"]')
                    element5.click()

                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    tbody = soup.find('tbody')
                    count_trs = len(tbody.find_all('tr'))
                    if (i == count_trs):
                        i=0
                        prevCount+=1

                    temp = prevCount
                    while (temp > 0) :
                        temp -= 1
                        prevElement = driver.find_element(By.XPATH, '//*[@class = "paginate_button previous"]')
                        prevElement.click()
                        time.sleep(1)

                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    tbody = soup.find('tbody')
                    row = soup.find_all('tr')[-(i+1)]
                    month = row.find_all('td')[-3].get_text()
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

                    driver.refresh()
                    response["matches"]["epf_history"][month] = result
                    # time.sleep(2)
                    my_set.add(month)
                    print(len(my_set))
                    print(my_set)
                    print(month)
                    if (len(my_set) == 5):
                        break
                    i+=1

                json_response = json.dumps(response, indent=2)
                print(json_response)
                driver.delete_all_cookies()
                driver.close()
                break
            if flag==1:
                break
        if flag==1:
            break

thread1 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ABHIJEET KUMAR SINGH"))
# thread2 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "ROHIT VERMA"))
# thread3 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "BENAKA N"))
# thread4 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ADIL DASTGIR SHAIKH"))
# thread5 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "ABHIJEET KUMAR SINGH"))
# thread6 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "CHANDINI S GOWDA"))
# thread7 = threading.Thread(target=epfo_scrapping, args=("Hummingwave Technologies", "1718939", "MD ADNANUDDIN"))
# thread8 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "ABHIJEET KUMAR SINGH"))
# thread9 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "CHAITALI UMESH BHAGWAT"))
# thread10 = threading.Thread(target=epfo_scrapping, args=("JUSPAY TECHNOLOGIES PRIVATE LIMITED", "1406277", "BINDUSHREE B N"))
# thread11 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "AAKARSHAN CHAUHAN"))
# thread12 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "ABDUL KAYES N"))
# thread13 = threading.Thread(target=epfo_scrapping, args=("ZSCALER SOFTECH INDIA PVT LTD", "0042806", "ABHISHEK ASHOK KUMAR SINGH"))
# thread14 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "VUDUGULA ANJU GOUD"))
# thread15 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "ZARANA GAURAV CHINTAL"))
# thread16 = threading.Thread(target=epfo_scrapping, args=("AMAZON DEVELOPMENT CENTRE (INDIA) PRIVATE LIMITED", "0026858", "ABHISHEK ASHOK KUMAR SINGH"))
# thread17 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "AAYUSH KUMAR"))
# thread18 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "UMMER FAROOK KASSIM"))
# thread19 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "TUSHAR DHANAI"))
# thread20 = threading.Thread(target=epfo_scrapping, args=("COLGATE- PALMOLIVE(INDIA) LIMITED", "0010647", "VARSHA SHETTY"))
# thread21 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ABHIJEET KUMAR SINGH"))
# thread22 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "ROHIT VERMA"))
# thread23 = threading.Thread(target=epfo_scrapping, args=("Finnable", "2114176", "BENAKA N"))
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
# thread14.start()
# thread15.start()
# thread16.start()
# thread17.start()
# thread18.start()
# thread19.start()
# thread20.start()
# thread21.start()
# thread22.start()
# thread23.start()
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
# thread14.join()
# thread15.join()
# thread16.join()
# thread17.join()
# thread18.join()
# thread19.join()
# thread20.join()
# thread21.join()
# thread22.join()
# thread23.join()
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
