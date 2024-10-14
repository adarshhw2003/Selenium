from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time;

driver = webdriver.Chrome()
query = "laptop"
fileno = 0
for i in range(1, 20):
    driver.get(f"https://www.amazon.in/s?k={query}&page={i}&crid=2FM0ACFC13V3N&qid=1727072823")
    elems = driver.find_elements(By.CLASS_NAME, "puis-card-container")
    print(f"page no {i}")
    print(f"{len(elems)} itmes found")
    for elem in elems:
        d  = elem.get_attribute("outerHTML")
        with open(f"data/{query}_{fileno}.html", "w", encoding="utf-8") as f:
            f.write(d)
            fileno += 1
driver.close()
