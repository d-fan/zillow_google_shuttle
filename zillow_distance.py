#!/usr/bin/python

import requests
import sys
import cPickle as pickle
import xml.etree.ElementTree as ElementTree
from geopy.distance import great_circle


"""
Instructions for url:
1) Browse to desired area and property types in Zillow (set price, num beds, etc.)
2) Open Developer Tools > Network
3) Filter to "getresults"
4) Paste in the request URL
"""
url = "http://www.zillow.com/search/GetResults.htm?spt=homes&status=000010&lt=000000&ht=111101&pr=,2063322&mp=,7500&bd=4%%2C&ba=0%%2C&sf=,&lot=,&yr=,&pho=0&pets=0&parking=0&laundry=0&pnd=0&red=0&zso=0&days=any&ds=all&pmf=0&pf=0&zoom=9&rect=-123072281,37016260,-121287003,37973974&p=1&sort=featured&search=maplist&disp=1&listright=true&isMapSearch=true&zoom=9"


class KMLWrapper:
	"""
	Convenience class for dealing with KML's dialect of XML. I couldn't find a
	good KML library that is also convenient to use. This is kludgy, but works
	"""

	def __init__(self, tree, namespace):
		self.tree = tree
		self.namespace = namespace

	def __getitem__(self, index):
		"""
		Gets all children with the given tag name, converting them to 
		KMLWrappers as well
		"""
		return map(lambda t: KMLWrapper(t, self.namespace), self.tree.findall(self.namespace + index))

	def __repr__(self):
		return str(self.tree.tag)[len(self.namespace):]

	def _has_child(self, cls, text=None):
		"""
		Return true if this tree has a child of the given class and optionally
		with the specified text
		"""
		children = self[cls]

		# Only checking for existence
		if text == None and children:
			return True

		# Check attributes for value
		if self.tree.get(cls) == text:
			return True

		# Check if there is a child with the right value
		for child in children:
			if child.tree.text == text:
				return True

		return False

	def get_all(self, cls, **kwargs):
		"""
		Gets all subtrees with a given class with children whose text contains
		the values specified in kwargs
		"""
		candidates = self[cls]
		results = []
		for candidate in candidates:
			# If everything provided in **kwargs matches
			if all([candidate._has_child(key, value) for key, value in kwargs.iteritems()]):
				results.append(candidate)
		return results

	def get(self, cls, **kwargs):
		results = self.get_all(cls, **kwargs)
		if results:
			return results[0]


class Location(object):
	def __init__(self, lat, lng):
		self.lat = lat
		self.lng = lng

	def location(self):
		return (self.lat, self.lng)

	def dist(self, other):
		return great_circle(self.location(), other.location()).miles


class Stop(Location):
	def __init__(self, name, lat, lng):
		super(Stop, self).__init__(lat, lng)
		self.name = name

	def __repr__(self):
		return self.name


class Listing(Location):
	def __init__(self, zpid, lat, lng):
		super(Listing, self).__init__(lat, lng)
		self.zpid = zpid

	def __repr__(self):
		return str(self.zpid)

	def url(self):
		return "http://www.zillow.com/homedetails/%d_zpid/" % self.zpid


def parse_shuttle_stops(filename):
	tree = ElementTree.parse(filename)
	namespace = "{http://www.opengis.net/kml/2.2}"
	stops = []

	# Get all "Shuttle stops" placemarks (i.e. all locations of shuttle stops)
	placemarks = KMLWrapper(tree.getroot(), namespace) \
		.get("Document", name="GBus Shuttle Stops - Noogler") \
		.get("Folder", name="Shuttle stops") \
		.get_all("Placemark")

	for p in placemarks:
		# Create a Stop object from lat, lng data
		data = p.get("ExtendedData")

		name = p.get("name").tree.text

		lat = data.get("Data", name="stopLatitude") \
				.get("value") \
				.tree.text

		lng = data.get("Data", name="stopLongitude") \
				.get("value") \
				.tree.text

		stops.append(Stop(name, lat, lng))
	return stops

def get_listings():
	if len(sys.argv) == 2 and sys.argv[1] == "mock":
		# Load if run with "mock" as first argument
		properties = pickle.load(open("properties.pickle", "r"))
	else:
		# Create and send request
		r = requests.get(url)

		# JSON-ify for easy traversal
		results = r.json()

		# Get the list of properties
		properties = results['map']['properties']

		# Cache so that we don't have to make a web request each time
		pickle.dump(properties, open("properties.pickle", "w"))

	ret = []
	for p in properties:
		# Property structure is [id, lat, lng, ...]
		# Zillow multiplies lat, lng by 1000000 to get integers. Convert back to floats
		ret.append(Listing(p[0], p[1] / 1000000., p[2] / 1000000.))
	return ret

def compare_listings():
	listings = get_listings()
	stops = parse_shuttle_stops("GBus Shuttle Stops - Noogler.kml")
	for listing in listings:
		for stop in stops:
			if listing.dist(stop) < 0.5:	# 0.5 Miles
				print listing.url()
				print "   ", stop, "Distance:", listing.dist(stop)

compare_listings()