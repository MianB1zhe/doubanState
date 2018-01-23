# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from myfunc import getBooksAll,bookdata,getbookyears,importcsv
from myfunc import taglist,piclist,countmessage,deleteDataAll,deleteData
import re
import os
import csv

# Create your views here.
def hello(request):
    return HttpResponse('hello world!')

def blog(request):
    return render_to_response('blog.html')

def booksearch(request):
    # return HttpResponse('hello')
    return render_to_response('booksearch.html')

def doubanbooks(request):
    try:
        mainpage = request.GET.get('mainpage')
        userid = mainpage.split('people/')[1].split('/')[0]
        getBooksAll(userid,'read')
        years = getbookyears(userid)
        message = countmessage(userid,years[0],years[-1])
        data = bookdata(userid,years)
        tlist = taglist(userid)
        plist = piclist(userid)
        return render_to_response('books.html',{'countmessage':message,'userid':userid,'years':years,'data':data,'list':tlist,'piclist':plist})
    except Exception as e:
        message = str(e) + " ,please check your url or try later !"  
        return render_to_response('booksearch.html',{'urlerror':message})

def csvdownload(request):
    try:
        userid = request.GET.get('userid')
        yearlist = getbookyears(userid)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment;filename="{0}.csv"'.format(userid)
        wb = csv.writer(response)
        importcsv(wb,userid,yearlist)
        return response 
    except Exception as e:
        return HttpResponse(e) 
    

def about(request):
    return render_to_response('about.html')

def deletedata(request):
    userid = request.GET.get('userid')
    if userid:
        deleteData(userid)
        return HttpResponse(userid + "'s data deleted! You can fresh page again!")
    else:
        deleteDataAll()
        return HttpResponse('All Data deleted!')
