from google.appengine.ext import bulkload
from google.appengine.api import datastore_types
from google.appengine.ext import search

class TramInfoLoader(bulkload.Loader):
	def __init__(self):
		bulkload.Loader.__init__(self, 'TramInfo',
													[ ('tracker_id', str), ('location', str) ])

	def HandleEntity(self, entity):
		ent = search.SearchableEntity(entity)
		return ent

if __name__ == '__main__':
	bulkload.main(TramInfoLoader())
