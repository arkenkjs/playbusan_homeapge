from urllib.request import urlopen
from bs4 import BeautifulSoup


# 네이버의 베스트셀러 웹페이지를 가져옵니다.
html = urlopen('https://book.naver.com/bestsell/bestseller_list.nhn?cp=yes24&cate=001001044&bestWeek=2020-01-1&indexCount=2&type=list')
bsObject = BeautifulSoup(html, "html.parser")


# 책의 상세 웹페이지 주소를 추출하여 리스트에 저장합니다.
book_page_urls = []
for index in range(0, 25):
    dl_data = bsObject.find('dt', {'id':"book_title_"+str(index)})
    link = dl_data.select('a')[0].get('href')
    book_page_urls.append(link)



# 메타 정보와 본문에서 필요한 정보를 추출합니다.  
for index, book_page_url in enumerate(book_page_urls):
    html = urlopen(book_page_url)
    bsObject = BeautifulSoup(html, "html.parser")


    title = bsObject.find('meta', {'property':'og:title'}).get('content')
    author = bsObject.find('dt', text='저자').find_next_siblings('dd')[0].text.strip()
    image = bsObject.find('meta', {'property':'og:image'}).get('content')
    url = bsObject.find('meta', {'property':'og:url'}).get('content')

    dd = bsObject.find('dt', text='가격').find_next_siblings('dd')[0]
    salePrice = dd.select('div.lowest strong')[0].text
    originalPrice = dd.select('div.lowest span.price')[0].text

    print(index+1, title, author, image, url, originalPrice, salePrice)