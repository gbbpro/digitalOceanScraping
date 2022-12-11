import os,time
import grequests
import requests, csv
from selectolax.parser import HTMLParser

dir_path = os.path.dirname(os.path.realpath(__file__))

brands = ['keen','merrell','adidas', 'prana','saucony','oneill', 'dakine','kuhl','salomon']

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
    reqs = [grequests.get(link) for link in urls]
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
        parsed = element.text(strip = True).replace('$','')
        if parsed != '':
            return float(parsed)
    except AttributeError as err:
        return

def parseResp(resp):
    results = []
    turpleres = []
    for r in resp:
        page = HTMLParser(r.text)
        url  = r.url
        title = textParse(page.css_first('h1'))
        try:
            item_number = textParse(page.css_first('span.item-number')).split('#')[-1]
        except:
            item_number = 'n/a'
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

        rei = ((title,item_number,price,original,discount,rating, ratingNum))
        turpleres.append(rei)
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
    return results

def toCsv(data,brand):
    fieldnames = []
    for dat in data:
        keys = list(dat.keys())
        for key in keys:
            if key not in fieldnames:
                fieldnames.append(key)
    with open(f'{dir_path}/reiCsv-s/rei-{brand}.csv','w', encoding = 'utf-8') as f:
        writer = csv.DictWriter(f, fieldnames= fieldnames)
        writer.writeheader()
        writer.writerows(data)
    return
if __name__ == "__main__":
    for brand in brands:
        time.sleep(2)
        
        response = getResponse(brand=brand)


        urls = getUrls(response)
        pages = getPage(urls)

        data = parseResp(pages)

        toCsv(data,brand)


