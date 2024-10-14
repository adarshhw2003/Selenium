from bs4 import BeautifulSoup
import os
import pandas as pd

d = {'title': [], 'price': [], 'link': [] }
for file in range(467):
    try:
        with open(f"data/laptop_{file}.html") as f:
            html_doc = f.read()
        soup = BeautifulSoup(html_doc, 'html.parser')
        t = soup.find('h2')
        title = t.get_text()

        l = t.find('a')
        link = "https://amazon.in/" + l['href']

        p = soup.find('span', class_ = 'a-price-whole')
        price = p.get_text()
        d['title'].append(title)
        d['price'].append(price)
        d['link'].append(link)
    except Exception as e:
        print(e)

df = pd.DataFrame(data=d)
df.to_csv("data.csv")