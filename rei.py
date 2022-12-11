import os
import grequests
import requests, csv, sqlite3
from selectolax.parser import HTMLParser
from reiheaders import headers

dir_path = os.path.dirname(os.path.realpath(__file__))

#brands = ['adidas',      'cannondale',  'keen',        'marmot',     'oneill',     'saucony', 'kelty','colombia','gregory','saloman','bern',        'dakine',      'kuhl',        'merrell',     'prana' ]

brands =['adidas', 'cannondale', 'saloman']

def getResponse(brand):

    url = f'https://www.rei.com/rei-garage/b/{brand}&pagesize=90'
    resp = requests.get(url=url)
    return resp.text

def getUrls(resp):
    page = HTMLParser(resp)
    baseUrl= 'https://www.rei.com'
    clean_links = []
    links = [baseUrl + link.attributes['href'] for link in page.css('.pPe0GNuagvmEFURs1Q_vm a')]
    for link in links:
        if link not in clean_links:
            clean_links.append(link)
    return clean_links

def getPage(urls):
    reqs = [grequests.get(link, headers = headers, timeout = 1) for link in urls]
    resp = grequests.map(reqs)
    return resp

def textParse(element):

    try:
        parsed = element.text(strip = True)
        parsed = parsed.replace('$','')
        return parsed 
    except AttributeError as e:
        print(e)
        return

def floatParse(element):
    try:
        parsed =element.text(strip = True).replace('$','')
        if parsed != '':
            return float(parsed)
        else:
            return 0.0
    except AttributeError as err:
        return

def parseResp(resp):
    results = []
    tupleres = []
    for r in resp:
        page = HTMLParser(r.text)
        url  = r.url
        title = textParse(page.css_first('h1'))
        try:
            item_number = textParse(page.css_first('span.item-number')).split('#')[-1]
        except:
            item_number = 'na'
        price = floatParse(page.css_first('span.price-value'))
        original = floatParse(page.css_first('span.compare-value'))
        try:
            discount = round((original-price) / original * 100, 2)
        except:
            discount = 0.00
        
        ratingCount = textParse(page.css_first('span.cdr-rating__count_11-3-1'))
        try:
            rating = ratingCount[0:3]
            ratingNum = ratingCount[3:].replace('Reviews','')
        except:
            rating = 0
            ratingNum = 0
        specs = page.css('tr.tech-specs__row')
        techSpecs = {th.css_first('th').text(strip = True) : th.css_first('td p').text(strip=True) for th in specs}

        
 
        items = {
            'url': url,
            'discount%': discount,
            'title': title,
            'item_number': item_number,
            'price': price,
            'original': original,
            'rating': rating,
            'ratingNum': ratingNum,
        
        }
        items.update(techSpecs)
        results.append(items)
        titems = (item_number,title, price, original, rating, ratingNum)
        tupleres.append(titems)
    return tupleres

if __name__ == "__main__":
    for brand in brands:
        response = getResponse(brand=brand)


        urls = getUrls(response)
        pages = getPage(urls)

        data = parseResp(pages)

        con = sqlite3.connect(f'{dir_path}/rei.db')

        cur = con.cursor()

        cur.execute(f"""CREATE TABLE IF NOT EXISTS {brand}(
            item_number TEXT PRIMARY KEY,
            title TEXT,
            price REAL, 
            original REAL, 
            rating REAL, 
            ratingNum REAL
        )""")

        with con:
            cur.executemany(f"""INSERT OR IGNORE INTO {brand} VALUES(?,?,?,?,?,?)""", data)

