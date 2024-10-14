from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time;

driver = webdriver.Chrome()
query = "laptop"
for i in range(1, 5):
    driver.get(f"https://www.amazon.in/s?k={query}&page={i}&crid=2FM0ACFC13V3N&qid=1727072823")
    elems = driver.find_elements(By.CLASS_NAME, "puisg-row")
    print(f"page no {i}")
    print(f"{len(elems)} itmes found")
    for elem in elems:
        print(elem.text)
driver.close()
