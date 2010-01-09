from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import mail
from django.utils import simplejson

import cgi
import re
import ClientForm
import logging
import sys
import traceback

class TramInfo(db.Model):
    tracker_id = db.StringProperty(required=True)
    location = db.StringProperty(required=True)



class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Worqbench')



# Sample test queries:
# curl 'http://localhost:8080/listTrams' --data 'stop=1234'

class ListTrams(webapp.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        finalResults = []
        memKey = ''

        # Get the parameters
        stop = cgi.escape(self.request.get('stop'))
        #logging.info("LT: " + stop + ".")
        if stop == "":
            returnError(self, "Invalid queries.")
            return

        memKey = stop
        memVal = memcache.get(memKey)
        if memVal is not None:
            self.response.out.write(memVal)
            return

        # Get the HTML data
        homePageContent = ''
        homeAddress = "http://www.yarratrams.com.au/ttweb/default.aspx"
        try:
            homePage = urlfetch.fetch(homeAddress)
            if homePage.status_code != 200:
                raise Exception("")
            homePageContent = homePage.content
        except:
            returnError(self, "Service unavailable.", "WARNING")
            return

        try:
            homePageForms = ClientForm.ParseFile(homePageContent, homeAddress, backwards_compat=False)
            form = homePageForms[0]
            form["txtTrackerID"] = stop
            formSubmit = form.click()
            formSubmitAddress = formSubmit.get_full_url()
            formSubmitData = formSubmit.get_data()
            formSubmitPage = urlfetch.fetch(formSubmitAddress, payload=formSubmitData, method='POST')
            rawData = formSubmitPage.content

            #fileEncoding = "iso-8859-1"
            #dataString = rawData.decode(fileEncoding)
            #dataString = dataString.encode("ascii", "ignore")
            dataString = rawData
        except:
            returnError(self, "Service unavailable.", "ERROR")
            return

        ## START OF DATA PROCESSING
        try:
            data0 = re.findall('<option value="(.*?)">.*?</option>', dataString, re.DOTALL)
            resultDetails = []

            if len(data0) == 0:
                finalResults.insert(0, {'status': "WORQ-OK", 'message': "LT-NOTFOUND"})
                memVal = simplejson.dumps(finalResults)
                memcache.set(key = memKey, value = memVal, time = 30)
                self.response.out.write(memVal)
                return 
            
            for data1 in data0:
                resultDetails.append(data1)
                
            finalResults.append({'trams': resultDetails})

        except:
            returnError(self, "Processing error.", "ERROR")
            return
        ## DATA OUTPUT
        finalResults.insert(0, {'status': "WORQ-OK", 'message': "LT-OK"})

        ## TRAM LOCATION        
        tramLocation = ''
        locMemKey = "tramLocation" + stop
        locMemVal = memcache.get(locMemKey)
        if locMemVal is not None:
            tramLocation = locMemVal
        else:
            tramInfo = db.GqlQuery("SELECT * FROM TramInfo WHERE tracker_id = :1", stop).get()
            if tramInfo is None:
                tramLocation = '-'
            else:
                tramLocation = tramInfo.location
            memcache.set(key = locMemKey, value = tramLocation, time = 604800)

        finalResults.append({'location': tramLocation})

        memVal = simplejson.dumps(finalResults)
        memcache.set(key = memKey, value = memVal, time = 30)
        self.response.out.write(memVal)
        ## END OF DATA PROCESSING



# Sample test queries:
# curl 'http://localhost:8080/listArrivals' --data 'stop=1234&tram=Any'

class ListArrivals(webapp.RequestHandler):
    def post(self):
        self.response.headers['Content-Type'] = 'text/plain'
        finalResults = []
        memKey = ''

        # Get the parameters
        stop = cgi.escape(self.request.get('stop'))
        tram = cgi.escape(self.request.get('tram'))
        #logging.info("LA: " + stop + " " + tram + ".")
        if stop == "" or tram == "":
            returnError(self, "Invalid queries.")
            return

        memKey = stop + tram
        memVal = memcache.get(memKey)
        if memVal is not None:
            self.response.out.write(memVal)
            return

        # Get the HTML data
        homePageContent = ''
        homeAddress = "http://www.yarratrams.com.au/ttweb/default.aspx"
        try:
            homePage = urlfetch.fetch(homeAddress)
            if homePage.status_code != 200:
                raise Exception("")
            homePageContent = homePage.content
        except:
            returnError(self, "Service unavailable.", "WARNING")
            return

        try:
            homePageForms = ClientForm.ParseFile(homePageContent, homeAddress, backwards_compat=False)
            form = homePageForms[0]
            form["txtTrackerID"] = stop
            formSubmit = form.click()
            formSubmitAddress = formSubmit.get_full_url()
            formSubmitData = formSubmit.get_data()
            formSubmitPage = urlfetch.fetch(formSubmitAddress, payload=formSubmitData, method='POST')
            rawData = formSubmitPage.content

            # TODO: Need to check whether the stop is valid or not.

            homePageForms = ClientForm.ParseFile(rawData, homeAddress, backwards_compat=False)
            form = homePageForms[0]
            form["txtTrackerID"] = stop
            form["ddlRouteNo"] = [tram]
            formSubmit = form.click()
            formSubmitAddress = formSubmit.get_full_url()
            formSubmitData = formSubmit.get_data()
            formSubmitPage = urlfetch.fetch(formSubmitAddress, payload=formSubmitData, method='POST')
            rawData = formSubmitPage.content

            #fileEncoding = "iso-8859-1"
            #dataString = rawData.decode(fileEncoding)
            #dataString = dataString.encode("ascii", "ignore")
            dataString = rawData
        except ClientForm.ItemNotFoundError:
            finalResults.insert(0, {'status': "WORQ-OK", 'message': "LA-NOTFOUND"})
            memVal = simplejson.dumps(finalResults)
            memcache.set(key = memKey, value = memVal, time = 30)
            self.response.out.write(memVal)
            return 
        except:
            returnError(self, "Service unavailable.", "ERROR")
            return

        ## START OF DATA PROCESSING
        try:
            data0 = re.findall('<td align="center">(.*?)</td>.*?<td>(.*?)</td>.*?<td align="right">(.*?)</td>', dataString, re.DOTALL)
            resultUpdateTime = re.findall('Results as at(.*?)</td>', dataString, re.DOTALL) 
            resultDetails = []
            
            for data1 in data0:
                resultRoute = re.sub('\s', '', data1[0])
                resultDestination = re.sub('\r\s*', '', data1[1])
                resultTime = re.sub('\r\s*', '', data1[2])
                resultTime = re.sub('<br/> ', '', resultTime)
                resultDetails.append(resultRoute + "#" + resultDestination + "#" + resultTime)
                
            finalResults.append({'arrivals': resultDetails})
            resultUpdateTime[0] = re.sub('\r\s*', '', resultUpdateTime[0])
            finalResults.append({'update': resultUpdateTime[0]})

        except:
            returnError(self, "Processing error.", "ERROR")
            return
        ## DATA OUTPUT
        finalResults.insert(0, {'status': "WORQ-OK", 'message': "LA-OK"})
        memVal = simplejson.dumps(finalResults)
        memcache.set(key = memKey, value = memVal, time = 30)
        self.response.out.write(memVal)
        ## END OF DATA PROCESSING



application = webapp.WSGIApplication([('/', MainPage), 
    ('/listTrams', ListTrams),
    ('/listArrivals', ListArrivals)
    ], debug=True)

def returnError(handler, message, level="INFO"):
    reqPath = handler.request.path
    reqBody = handler.request.body
    logMesg = message + " (" + reqPath + " " + reqBody + ")"

    if level == "INFO":
        logging.info(logMesg)
    elif level == "WARNING":
        logging.warning(logMesg)
    elif level == "ERROR":
        logMesgDetail = ""
        et, ev, tb = sys.exc_info()
        logMesgDetail += str(et) + " "
        logMesgDetail += str(ev) + " "
        while tb:
            co = tb.tb_frame.f_code
            line_no = "#" + str(traceback.tb_lineno(tb)) + " "
            logMesgDetail += line_no 
            tb = tb.tb_next
        logging.error(logMesg + " " + logMesgDetail)
        mail.send_mail(sender = "info@worqbench.com",
              to = "info+appengine@worqbench.com",
              subject = "Meltrams ERROR",
              body = logMesg + " " + logMesgDetail)

    finalResults = []
    finalResults.append({'status': "WORQ-ERROR", 'message': message})
    handler.response.out.write(simplejson.dumps(finalResults))

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
