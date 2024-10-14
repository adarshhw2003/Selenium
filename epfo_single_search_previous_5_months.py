from selenium import webdriver
from datetime import datetime
import pandas as pd
import re
import cv2
import pytesseract
import numpy as np
import os
import base64
import io
import time
import calendar
from PIL import Image
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

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
                image.save("ss.png")
                image = cv2.imread("ss.png")
                captcha_text = bypass_captcha(image)
                print(captcha_text)
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
                onclickText = soup.find('div', id='tablecontainer3').find('a')
                result = re.search(r"\('(.*?)'\)", onclickText['onclick'])
                part = result.group(1)
                # print(part)
                newURL = "https://unifiedportal-emp.epfindia.gov.in" + part
                driver.get(newURL)

                i=4
                while i>=0:

                    element5 = driver.find_element(By.XPATH, '//*[@data-dt-idx = "6"]')
                    element5.click()

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
                        print(company_name, name, "(", month_names[i], ") -> NO")
                    except NoSuchElementException:
                        print(company_name, name, "(", month_names[i], ") -> YES")

                    driver.refresh()
                    # time.sleep(2)
                    i-=1

                driver.delete_all_cookies()
                driver.close()
                break
            if flag==1:
                break
        if flag==1:
            break

epfo_scrapping("Finnable", "2114176", "ABHIJEET KUMAR SINGH")