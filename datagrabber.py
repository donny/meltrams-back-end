import urllib
import re
import time
import pickle

tram_data = {}

route_numbers = ['1', '3', '5', '6', '8', '16', '19', '24', '30', '31', 
'48', '55', '57', '59', '64', '67', '70', '72', '75', '78', 
'79', '82', '86', '96', '109', '112']

for routeno in route_numbers:

	upstops = ['1', '0']

	for upstop in upstops:

		address = 'http://www.yarratrams.com.au/ttweb/Stops.aspx?routeno=' + routeno + '&upstop=' + upstop

		url_data = urllib.urlopen(address)
		raw_data = url_data.read()
		url_data.close()

		data0 = re.findall('>Stop (.*?)&nbsp;(.*?)<.*?>Tracker ID : (.*?)<', raw_data, re.DOTALL)

		for data1 in data0:
			stopAddress = data1[1]
			stopTracker = data1[2]
			stopAddress = re.sub('&nbsp;', ' ', stopAddress)
			stopAddress = re.sub('^\s+', '', stopAddress)
			stopAddress = re.sub('&', 'and', stopAddress)
			
			#print stopAddress + " " + stopTracker
			tram_data[stopTracker] = stopAddress
			
		print "Tram: " + routeno + " (" + upstop + ")"
		time.sleep(2)
			
tram_file = open('/tmp/tram_data.pickle', 'w')
pickle.dump(tram_data, tram_file)
tram_file.close()

tram_file = open('/tmp/tram_data.csv', 'w')
for key in tram_data:
	tram_file.write(key + "," + tram_data[key] + "\n")
tram_file.close()

print "DONE"