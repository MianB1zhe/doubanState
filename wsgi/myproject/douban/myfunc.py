# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import requests
import json
import pymongo
import re
import csv

count = 0
#conn = pymongo.MongoClient('127.0.0.1',27017)
conn = pymongo.MongoClient()
db = conn['doubanstate']
#db.authenticate('Ubuntu', '')
booktable = db['book']
booknum = db['booknum']

TW1 = re.compile(u"台币")
TW2 = re.compile(u"台幣")
TW3 = re.compile(u"臺幣")
TW4 = re.compile(u"NT")
TW5 = re.compile(u"TW")
HK1 = re.compile(u"HK")
HK2 = re.compile(u"港币")
JP1 = re.compile(u"JPY")
JP2 = re.compile(u"円")
EU1 = re.compile(u"EUR")
EU2 = re.compile(u"€")
UN1 = re.compile(u"GBP")
UN2 = re.compile(u"£")
US1 = re.compile(u"US")
US2 = re.compile(u"\\$")
CN1 = re.compile(u"元")
CN2 = re.compile(u"CNY")
CN3 = re.compile(u"RMB")
NU1 = re.compile(u"\\d+\\.\\d+")
NU2 = re.compile(u"\\d+")

def getBooks(userid,start,counts,status):
    global count
    url = 'https://api.douban.com/v2/book/user/{}/collections?start={}&count={}&status={}'.format(userid,start,counts,status)
    page = requests.get(url).content
    con = json.loads(page)
    count = count + con['count']
    for book in con['collections']:
        title = book['book']['title']
        bookurl = book['book']['url']
        image = book['book']['image']
        dates = book['updated'].split(' ')[0]
        year = dates.split('-')[0]
        month = dates.split('-')[1]
        rating = book['book']['rating']['average']
        tags = [tag['name'] for tag in book['book']['tags']]
        price = book['book']['price']
        try:
            pt = getPrice(price)
        except:
            pt = '0/人民币'

        data ={'title':title,'bookurl':bookurl,'image':image,'date':dates,'year':year,'month':month,'rating':rating,'tags':tags,'price':pt}
        booktable.insert_one(data)

def getPrice(priceText):
    pt = priceText.strip().replace(',','').upper()

    if TW1.search(pt) or TW2.search(pt) or TW3.search(pt) or TW4.search(pt) or TW5.search(pt):
        price = NU1.findall(pt) or NU2.findall(pt)
        price = price[0] + '/台币'
    elif HK1.search(pt) or HK2.search(pt):
        price = NU1.findall(pt) or NU2.findall(pt)
        price = price[0] + '/港币'
    elif JP1.search(pt) or JP2.search(pt):
        price = NU1.findall(pt) or NU2.findall(pt)
        price = price[0] + '/日币'
    elif EU1.search(pt) or EU2.search(pt):
        price = NU1.findall(pt) or NU2.findall(pt)
        price =price[0] + '/欧元'
    elif UN1.search(pt) or UN2.search(pt):
        price = NU1.findall(pt) or NU2.findall(pt)
        price =price[0] + '/英镑'    
    elif US1.search(pt) or US2.search(pt):
        price = NU1.findall(pt) or NU2.findall(pt)
        price = price[0] + '/美元'
    elif CN1.search(pt) or CN2.search(pt) or CN3.search(pt) or NU1.search(pt) or NU2.search(pt):
        price = NU1.findall(pt) or NU2.findall(pt)
        price = price[0] + '/人民币'
    else:
        price = '0/人民币'
    return price

def gettotal(userid,status):
    url = 'https://api.douban.com/v2/book/user/{}/collections?status={}'.format(userid,status)
    page = requests.get(url).text
    con = json.loads(page)
    total = con['total']
    return total

def getBooksAll(userid,status):
    global count,booktable
    count = 0
    booktable = db[userid]
    exits = booktable.find().count()
    total = gettotal(userid,status)
    try:
        booknum.remove({'userid':userid})
    except:
        pass   
    booknum.insert_one({'userid':userid,'booknum':total})
    total = total - exits
    while count<total:
        getBooks(userid,count,total-count,status)

def getbookyears(userid):
    global booktable
    booktable = db[userid]
    data = []
    yearlist = []
    for year in booktable.find().distinct('year'):
        yearlist.append(year.encode('utf-8'))
    yearlist.sort(key=lambda x:int(x),reverse=True)
    return yearlist

def bookdata(userid,yearlist):
    global booktable
    booktable = db[userid]
    data = []
    months = ['01','02','03','04','05','06','07','08','09','10','11','12']
    month_name = ['Jan','Feb','Mar','Apr','May','June','July','Aug','Sept','Oct','Nov','Dec']
    for year in yearlist:
        year_count = booktable.find({'year':year}).count()
        month_count = []
        for month in months:
            book_month = booktable.find({'year':year,'month':month}).count()
            month_count.append(book_month)
        data_year = {
                        'y':year_count,
                        'drilldown':{
                                'name':year,
                                'categories':month_name,
                                'data':month_count,
                                    }
                    }
        data.append(data_year)
    return data

def countmessage(userid,thisyear,firstyear):
    global booktable
    booktable = db[userid]
    page = requests.get('https://api.douban.com/v2/user/'+userid)
    conn = json.loads(page.content)
    name = conn['name']
    total = booknum.find({'userid':userid})[0]['booknum']
    alluser = booknum.find().count()
    userorder = booknum.find({'booknum':{'$gt':total}}).count()
    thisnum = booktable.find({'year':thisyear}).count()
    thisprices = {}
    totalprices = {}
    for book in booktable.find({'year':thisyear}):
        price = book['price'].split('/')[0]
        pricetype = book['price'].split('/')[1]
        if pricetype not in thisprices:
            thisprices[pricetype] = round(float(price),0)
        else:
            thisprices[pricetype] += round(float(price),0)
    for book in booktable.find():
        price = book['price'].split('/')[0]
        pricetype = book['price'].split('/')[1]
        if pricetype not in totalprices:
            totalprices[pricetype] = round(float(price),0)
        else:
            totalprices[pricetype] += round(float(price),0)
    thisprices = sorted(list(thisprices.items()),key=lambda x:x[1],reverse=True)        
    totalprices = sorted(list(totalprices.items()),key=lambda x:x[1],reverse=True)
    dayperbook = round((float(thisyear)-float(firstyear))*360/total,1)
    message = name + ',您' + thisyear + '年已经在豆瓣读了' + str(thisnum) + '本书.<br>'
    tprice = ':'
    for p in thisprices:
        tprice = tprice + p[0] + str(p[1]) + ', ' 
    message += '您' + thisyear + '已读的书价值约为' + tprice + '还不错. <br><br>'
    message += '自' + firstyear + '年开始使用豆瓣，您已经阅读了' + str(total) + '本书.'
    message += '平均每' + str(dayperbook) + '天阅读一本.<br>'
    tprice = ':'
    for p in totalprices:
        tprice = tprice + p[0] + str(p[1]) + ', ' 
    message += '所有您' + '读过的书总价值约为' + tprice + '哈哈,继续努力！<br><br>'
    message += '目前共有' + str(alluser) + '位用户访问过本站,您的读书量排行第' + str(userorder+1) + ',加油！'
    return message

def taglist(userid):
    global booktable
    booktable = db[userid]
    taglist = {}
    for book in booktable.find():
        for tag in book['tags']:
            if tag not in taglist:
                taglist[tag] = 1
            else:
                taglist[tag] += 1
    taglist = sorted(list(taglist.items()),key=lambda x:x[1],reverse=True)    
    if len(taglist)>200:
        taglist = taglist[:200]
    taglist = json.dumps(taglist).decode('unicode-escape')
    return taglist

def piclist(userid):
    global booktable
    booktable = db[userid]
    piclist = []
    for book in booktable.find():
        picurl = book['image'].encode('utf-8')
        piclist.append(picurl)
    if len(piclist) > 100:
        piclist = piclist[:100]
    return piclist

def importcsv(wb,userid,yearlist):
    global booktable
    months = ['01','02','03','04','05','06','07','08','09','10','11','12']
    title = [' ','Jan','Feb','Mar','Apr','May','June','July','Aug','Sept','Oct','Nov','Dec','total']
    booktable = db[userid]
    #fi.write(codecs.BOM_UTF8)
    wb.writerow(['title','date','rating','price','bookurl'])
    for b in booktable.find():
        data = [b['title'].decode('utf-8').encode('gb2312','ignore'),b['date'],b['rating'],b['price'].decode('utf-8','ignore').encode('gb2312'),b['bookurl']]
        wb.writerow(data)
    wb.writerows([' ',' ',' '])
    wb.writerow(['bookcount'])
    wb.writerow(title)
    for year in yearlist:
        year_count = booktable.find({'year':year}).count()
        month_count = [year]
        for month in months:
            book_month = booktable.find({'year':year,'month':month}).count()
            month_count.append(book_month)
        month_count.append(year_count)
        wb.writerow(month_count)

def deleteDataAll():
    for table in db.collection_names():
        if not table.startswith('system'):
            db[table].drop()

def deleteData(userid):
    db[userid].drop()

if __name__ == '__main__':
    
    #bookdata('70276760')
    #piclist('70276760')
    #deleteDataAll()
    getBooksAll('doloresding','read')
    #countmessage('doloresding','2016','2009')
    yearlist = getbookyears('doloresding')
