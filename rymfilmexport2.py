import gevent.monkey
gevent.monkey.patch_all()
from fake_useragent import UserAgent
import os, re, sys, time, json, lxml.html, requests, random, traceback, csv, json
from lxml.html import fromstring
from itertools import cycle
from Proxies import Proxies 


def sanitise_text(text):
    return re.sub(r'\s+', ' ', text.strip())


def image_to_rating(elem):
    suffix = 'm.png'
    src = elem.get('src')
    image = os.path.basename(src)
    assert image.endswith(suffix)
    rating = int(image[:-len(suffix)])
    return rating


def get_first_if_one(elems):
    if len(elems) != 1:
        raise ValueError('{!r} has {} elements, expected 1'.format(elems, len(elems)))
    return elems[0]

def row_count():
    f=0
    with open('outputfile.csv', encoding='utf-8') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            if row:
                f=f+1   
    f=int(f/25)   
    return(f)

def parse_page(page, out, base_href):
    tree = lxml.html.fromstring(page)
    tree.make_links_absolute(base_href) 
    rating_table = get_first_if_one(tree.xpath('//table[@class="mbgen"]'))
    #l=row_count()
    #print("k:{} l={}".format(k, l))
    
    for row in rating_table.xpath('.//tr[td]'):
        film = row.xpath('.//a[@class="film"]//text()')
        rating = image_to_rating(get_first_if_one(row.xpath(r'.//img[@height="16"]')))
        film = ', '.join(sanitise_text(a) for a in film)
        out.append(
            {
                'Title': film,
                'Rating': rating,
            }
        )
    try:
        #print("tree path:",tree.xpath('//a[@class="navlinknext"]')[0].get('href'))
        return tree.xpath('//a[@class="navlinknext"]')[0].get('href')
    except IndexError:
        pass

ua = UserAgent()
def main():
    try:
        username = sys.argv[1]
    except IndexError:
        print('Usage: {} username'.format(sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    base_href = 'https://rateyourmusic.com'
    #c = 
    next_uri = '{}/film_collection/{}/r0.5-5.0/{}'.format(base_href, username, row_count()+1)
    headers = {'User-Agent': ua.random,
                'Referer': 'https://rateyourmusic.com/~{}'.format(username)}
    #headers = {
    #    'User-Agent':
    #        'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.11) ' 
    #        'Gecko/20101012 Firefox/3.6.11',
    #        #'Mozilla/5.0 (X11; Linux x86_64; rv:54.0) '
    #        #'Gecko/20100101 Firefox/54.0',
    #    'Referer': 'https://rateyourmusic.com/~{}'.format(username),
    #}
    output = []
    q = 0
    k=0 
    m=0
    i = row_count()+1
    p = Proxies() 
    p.get_proxies(260, 1)
    result = p.get_result()  
    while next_uri:
        proxy = result[q]
        req = requests.get(next_uri, headers=headers, proxies=proxy)
        req.raise_for_status()
        next_uri = parse_page(req.text, output, base_href)
        print('Parsed page {}'.format(i), file=sys.stderr)
        print("Next URL: {}".format(next_uri))
        i += 1
        q += 1
        if next_uri:
            # backoff to be nice to rym
            time.sleep((random.randint(12, 20)))
        with open('outputfile.csv', 'a', encoding='utf-8') as outfile:
            dw = csv.DictWriter(outfile, output[0].keys())
            #dw.writeheader()
            for row in output:
                if (m==0):
                    dw.writerow(row)
                else:
                    m-=1
        k+=1
        m=k*25
    #csvwriter = csv.writer(csv_data)
    #print(json.dumps(output))

if __name__ == '__main__':
    main()
    