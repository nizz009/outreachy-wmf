import json
# import os
import re
# import string
# import sys
# import _thread
import time
# import unicodedata
import urllib
import urllib.request
import urllib.parse
import datetime
import dateparser

import pywikibot
from pywikibot import pagegenerators

# file imports
import search_patterns

enwp = pywikibot.Site('en', 'wikipedia')
enwd = pywikibot.Site('wikidata', 'wikidata')
repo = enwd.data_repository()
encommons = pywikibot.Site('commons', 'commons')
globe_item = pywikibot.ItemPage(repo, 'Q2')

langs = { 
	'en': 'Q328', 
	'fr': 'Q8447', 
	'it': 'Q11920', 
	}

# helper functions
# from https://bitbucket.org/mikepeel/wikicode/src/master/wir_newpages.py
def getURL(url='', retry=True, timeout=30):
	raw = ''
	req = urllib.request.Request(url, headers={ 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0' })
	try:
		raw = urllib.request.urlopen(req, timeout=timeout).read().strip().decode('utf-8')
	except:
		sleep = 10 # seconds
		maxsleep = 100
		while retry and sleep <= maxsleep:
			print('Error while retrieving: %s' % (url))
			print('Retry in %s seconds...' % (sleep))
			time.sleep(sleep)
			try:
				raw = urllib.request.urlopen(req, timeout=timeout).read().strip().decode('utf-8')
			except:
				pass
			sleep = sleep * 2
	return raw

def get_precision(val):
	# print(val)
	if '.' in str(val):
		val = val.split('.')[1]
		length = len(val)
	else:
		length = 0
	if length >= 5:
		length = 5
	# print(len(val))
	return 10**-length

def calc_coord(params):
	# print(len(params))
	lat = False
	lon = False
	precision = False
	if len(params) >= 8:
		if 'S' in params[3] or 'N' in params[3]:
			lat = float(params[0]) + (float(params[1])/60.0)+(float(params[2])/(60.0*60.0))
			if 'S' in params[3]:
				lat = -lat
			lon = float(params[4]) + (float(params[5])/60.0)+(float(params[6])/(60.0*60.0))
			if 'W' in params[7] or 'O' in params[7]:
				lon = -lon
			precision = get_precision(params[2])/(60.0*60.0)
	if lat == False and len(params) > 2:
		if ('S' in params[2] or 'N' in params[2]) and len(params) >= 5:
			lat = float(params[0]) + (float(params[1])/60.0)
			if 'S' in params[2]:
				lat = -lat
			lon = float(params[3]) + (float(params[4])/60.0)
			if 'W' in params[5] or 'O' in params[5]:
				lon = -lon
			precision = get_precision(params[1])/(60.0)
		elif (params[1] == 'N' or params[1] == 'S') and len(params) >= 3:
			lat = float(params[0])
			lon = float(params[2])
			precision = get_precision(params[0])
			if params[1] == 'S':
				lat = -lat
			if params[3] == 'W' or params[3] == 'O':
				lon = -lon
		elif '.' in params[0] and '.' in params[1]:
			lat = float(params[0])
			lon = float(params[1])
			precision = get_precision(params[0])
		else:
			print(params)
			print('Something odd in calc_coord (1)')
			# return False, False, False
	elif '.' in params[0] and '.' in params[1]:
		lat = float(params[0])
		lon = float(params[1])
		precision = get_precision(params[0])

	if lat == False:
		print(params)
		print('Something odd in calc_coord (2)')
		# return False, False, False
	# print(lon)
	# print(lat)
	# print(precision)
	return lat, lon, precision

# deals with Wikipedia articles
class WpPage:
	"""
	List of methods:

	- getWpContents
	- printWpContents
	- searchWpPage
	- findInfobox
	- isProtected

	"""

	def __init__(self, page_name=''):
		if page_name:
			self.page_name = page_name
			self.page = pywikibot.Page(enwp, page_name)
			self.title = self.page.title()

	def getWpContents(self):
		""" Returns contents of a Wikipedia page """
		if self.page:
			return self.page.text
		else:
			return ''

	def printWpContents(self):
		""" Prints contents of a Wikipedia page """

		content = self.page.get()
		print(content)

		return 0

	def searchWpPage(self, props=''):
		""" 
		Searches for a Wp article in Wd

		@param props: dictionary of format {prop_id_1: [prop_values], prop_id_2: [prop_values]}
					prop_id: ID of the property used to match Wd item with Wp article
					prop_values: Property values associated with the prop_id

		@return value: title (Qvalue) of the Wd Item

		""" 

		page_title = self.page.title()
		page_title_ = page_title.split('(')[0].strip()
		searchitemurl = 'https://www.wikidata.org/w/api.php?action=wbsearchentities&search=%s&language=en&format=xml' % (urllib.parse.quote(page_title_))
		raw = getURL(searchitemurl)

		# searches and matches the items for the searched item
		if not '<search />' in raw:
			q_values = re.findall(r'id="(Q\d+)"', raw)
			for q_value in q_values:
				# get page for each Qval in search result
				itemfound = pywikibot.ItemPage(repo, q_value)
				item_dict = itemfound.get()

				flag = 0
				if 'P31' in itemfound.claims:
					for claim in item_dict['claims']['P31']:
						prop_id_value = claim.getTarget()
						if prop_id_value == 'Q4167410':
							print('Dsiambiguous page. Skipping...')
							flag = 1
							break
				if flag:
					continue

				prop_count = 0
				# check for each property criteria provided
				for prop_id in props.keys():
					prop_count += 1

					if not props[prop_id]:
						print('No property values for' + str(prop_id) + 'provided. Skipping the search.\n')
						continue

					# property exists in the Wd page
					if prop_id in itemfound.claims:
						itemfound_values = []
						for claim in item_dict['claims'][prop_id]:
							prop_id_value = claim.getTarget()
							prop_id_item_dict = prop_id_value.get()
							itemfound_values.append(prop_id_item_dict['labels']['en'])

						itemfound_values = [itemfound_value.replace('\xa0',' ') for itemfound_value in itemfound_values]

						itemfound_count = 0
						for itemfound_value in itemfound_values:
							if itemfound_value in props[prop_id]:
								itemfound_count += 1

						if itemfound_count >= (len(props[prop_id])/2):
							flag += 1
						else:
							break
					else:
						continue

				if flag >= (prop_count/2):
					return itemfound.title()
		else:
			print('Item doesn\'t exist.')
			return None

		print('No match was found.')

		return None

	def findInfobox(self, check_all=''):
		if self.page:
			text_screened = re.findall(r'\{\{Infobox .*[\n]*', self.page.text, re.DOTALL)
			if text_screened:
				text = text_screened[0].split('==')
				text = text[0].split('\n}}')
				result = search_patterns.infobox(page_text=text[0], check_all=check_all)
				# search_patterns.infobox(self.page.text)
				if result:
					return result
				return ''
		else:
			print('No page exists.')
			return None

	def isProtected(self):
		if self.page:
			if 'title="This article is' in self.page.text:
				return True
			return False
		else:
			print('No page exists.')
			return False


# deals with Wikidata articles
class WdPage:
	"""
	List of methods:

	- printWdContents
	- addWdProp
	- addFiles
	- addNumeric
	- addDate
	- addIdentifiers
	- checkClaimExistence
	- addImportedFrom
	- addQualifiers

	"""

	def __init__(self, wd_value='', page_name=''):
		if wd_value:
			self.page = pywikibot.ItemPage(enwd, wd_value)
		elif page_name:
			wp_page = pywikibot.Page(enwp, page_name)
			if wp_page:
				self.page = pywikibot.ItemPage.fromPage(wp_page)
			else:
				print('No wikipedia page exists')

		self.wd_value = self.page.title()

	def getWdContents(self):
		return self.page.get()

	def printWdContents(self):
		""" Prints contents of a Wikidata page """

		print(self.page.title())

		categories = self.page.get()

		for items in categories:
			try:
				print("Category: " + items)
				for item in categories[items]:
					try:
						print(categories[items][item])
					except:
						print("Error in browsing through items.")
				print("\n")
			except:
				print("Error in browsing through categories.")

		return 0

	def addWdProp(self, prop_id='', prop_value='', lang='', qualifier_id='', qualval_id='', confirm='', overwrite='', append=''):
		"""
		Adds a new property in Wikidata

		@param prop_id: ID of the property
		@param prop_value: ID or Value of property's value
		@param lang: language of Wikipedia artcile: for references
		@param qualifier_id: ID of the qualifier
		@param qualval_id: ID of the qualifier's value
		@param confirm: set to 'y' to avoid the confirmation message before adding a property

		@type all: string

		"""
		print(self.page.title())

		if prop_value and not re.search(r'Unknown', prop_value, re.IGNORECASE):
			try:
				if re.search(r'Q\d+', prop_value):
					new_prop_val = pywikibot.ItemPage(enwd, prop_value)
				else:
					searchitemurl = 'https://www.wikidata.org/w/api.php?action=wbsearchentities&search=%s&language=en&format=xml' % (urllib.parse.quote(prop_value))
					raw = getURL(searchitemurl)
					# print(raw)
					
					ids = list()
					# check for valid search result
					if not '<search />' in raw:
						m = re.findall(r'id="(Q\d+)"', raw)
						# print(m)

						for itemfoundq in m:
							itemfound = pywikibot.ItemPage(repo, itemfoundq)
							item_dict = itemfound.get()
							# print(prop_value)
							# print(item_dict['labels']['en'])
							# print('\n')
							flag = 0
							if 'P31' in itemfound.claims:
								for claim in item_dict['claims']['P31']:
									prop_id_value = claim.getTarget()
									# print(prop_id_value.title())
									if prop_id_value.title() == 'Q4167410':
										print('Disambiguous page. Skipping...')
										flag = 1
										break
							if flag:
								continue

							if prop_value.lower() == (item_dict['labels']['en']).lower():
								# print('hello')
								# new_prop_val = pywikibot.ItemPage(enwd, itemfoundq)
								ids.append(itemfoundq)
						if len(ids) > 1:
							print('multiple pages found')
							return
						else:
							new_prop_val = pywikibot.ItemPage(enwd, ids[0])

					else:
						print('No item page exists/Incorrect value provided.\n')

			except:
				print('Incorrect property value provided.\n')
				return 1

		self.page.get()
		if prop_id in self.page.claims:
			choice = ''
			if not append and not overwrite:
				choice = input('Property already exists. Select:\n\
					1 to skip\n\
					2 to over-write the existing property\n\
					3 to add another value to the property\n')

			if choice == '1':
				return

			elif choice == '2' or overwrite == 'y':
				self.page.removeClaims(self.page.claims[prop_id])
		
			elif choice > '3':
				print("Invalid choice.\n")
				return 1
	
		try:
			new_prop = pywikibot.Claim(enwd, prop_id)	
			new_prop.setTarget(new_prop_val)

			# confirmation
			if confirm.lower() == 'y':
				self.page.addClaim(new_prop, summary = u'Adding new property')
				# retrieving the updated page
				self.page = pywikibot.ItemPage(enwd, self.wd_value)
		
				if lang:
					self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
					# print("Reference added.")
				if qualifier_id and qualval_id:
					self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
					# print("Qualifier added.")

			else:
				print(new_prop)
				text = input("Do you want to save this property? (y/n) ")
				if text == 'y':
					self.page.addClaim(new_prop, summary = u'Adding new property')
					# retrieving the updated page
					self.page = pywikibot.ItemPage(enwd, self.wd_value)
			
					if lang:
						self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
						# print("Reference added.")
					if qualifier_id and qualval_id:
						self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
						# print("Qualifier added.")

		except:
			print('Error in adding new property.')

		return 0

	def addFiles(self, prop_id='', prop_value='', lang='', qualifier_id='', qualval='', qualval_id='', confirm='', overwrite='', append=''):
		""" Adds files from Commons to Wikidata """

		print(self.page.title())

		if prop_value:
			try:
				new_prop_val = pywikibot.FilePage(encommons, prop_value)
			except:
				print('Incorrect property value provided.\n')
				return 1

		self.page.get()
		if prop_id in self.page.claims:
			choice = ''
			if not append and not overwrite:
				choice = input('Property already exists. Select:\n\
					1 to skip\n\
					2 to over-write the existing property\n\
					3 to add another value to the property\n')

			if choice == '1':
				return

			elif choice == '2' or overwrite == 'y':
				self.page.removeClaims(self.page.claims[prop_id])
		
			elif choice > '3':
				print("Invalid choice.\n")
				return 1

		try:
			new_prop = pywikibot.Claim(repo, prop_id)	
			new_prop.setTarget(new_prop_val)

			if confirm.lower() == 'y':
				self.page.addClaim(new_prop, summary = u'Adding new file')
				self.page = pywikibot.ItemPage(enwd, self.wd_value)

				if lang:
					self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
					# print("Reference added.")
				if qualifier_id:
					if qualval_id:
						self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
					elif qualval:
						self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval=qualval, status=1)
					# print("Qualifier added.")

			else:
				# confirmation
				print(new_prop)
				text = input("Do you want to save this property? (y/n) ")
				if text == 'y':
					self.page.addClaim(new_prop, summary = u'Adding new file')
					self.page = pywikibot.ItemPage(enwd, self.wd_value)

					if lang:
						self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
						# print("Reference added.")
					if qualifier_id:
						if qualval_id:
							self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
						elif qualval:
							self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval=qualval, status=1)
						# print("Qualifier added.")

		except:
			print('Error in adding new file.')

		return 0

	def addMonolingualText(self, prop_id='', prop_value='', text_language='', lang='', qualifier_id='', qualval_id='', confirm='', overwrite='', append=''):
		""" Adds numeric values to Wikidata """

		print(self.page.title())

		if prop_value:
			try:
				val = pywikibot.WbMonolingualText(text=prop_value, language=text_language)
			except:
				print('Incorrect property value provided.\n')
				return 1

		self.page.get()
		if prop_id in self.page.claims:
			choice = ''
			if not append and not overwrite:
				choice = input('Property already exists. Select:\n\
					1 to skip\n\
					2 to over-write the existing property\n\
					3 to add another value to the property\n')

			if choice == '1':
				return

			elif choice == '2' or overwrite == 'y':
				self.page.removeClaims(self.page.claims[prop_id])
		
			elif choice > '3':
				print("Invalid choice.\n")
				return 1

		try:
			new_prop = pywikibot.Claim(repo, prop_id)
			# print('hello')
			new_prop.setTarget(val)
			# print(val)

			if confirm.lower() == 'y':
				self.page.addClaim(new_prop, summary = u'Adding new string/monolingual text')
				self.page = pywikibot.ItemPage(enwd, self.wd_value)

				if lang:
					self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
					# print("Reference added.")
				if qualifier_id and qualval_id:
					self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
					# print("Qualifier added.")

			else:
				# confirmation
				print(new_prop)
				text = input("Do you want to save this property? (y/n) ")
				if text == 'y':
					self.page.addClaim(new_prop, summary = u'Adding new string/monolingual text')
					self.page = pywikibot.ItemPage(enwd, self.wd_value)

					if lang:
						self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
						# print("Reference added.")
					if qualifier_id and qualval_id:
						self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
						# print("Qualifier added.")

		except:
			print('Error in adding monolingual text.')

		return 0


	def addNumeric(self, prop_id='', prop_value='', lang='', qualifier_id='', qualval_id='', confirm='', overwrite='', append=''):
		""" Adds numeric values to Wikidata """

		print(self.page.title())

		if prop_value:
			try:
				val = pywikibot.WbQuantity(amount=prop_value, site=enwp)
			except:
				print('Incorrect property value provided.\n')
				return 1

		self.page.get()
		if prop_id in self.page.claims:
			choice = ''
			if not append and not overwrite:
				choice = input('Property already exists. Select:\n\
					1 to skip\n\
					2 to over-write the existing property\n\
					3 to add another value to the property\n')

			if choice == '1':
				return

			elif choice == '2' or overwrite == 'y':
				self.page.removeClaims(self.page.claims[prop_id])
		
			elif choice > '3':
				print("Invalid choice.\n")
				return 1

		try:
			new_prop = pywikibot.Claim(repo, prop_id)
			# print('hello')
			new_prop.setTarget(val)
			# print(val)

			if confirm.lower() == 'y':
				self.page.addClaim(new_prop, summary = u'Adding new numeric value')
				self.page = pywikibot.ItemPage(enwd, self.wd_value)

				if lang:
					self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
					# print("Reference added.")
				if qualifier_id and qualval_id:
					self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
					# print("Qualifier added.")

			else:
				# confirmation
				print(new_prop)
				text = input("Do you want to save this property? (y/n) ")
				if text == 'y':
					self.page.addClaim(new_prop, summary = u'Adding new numeric value')
					self.page = pywikibot.ItemPage(enwd, self.wd_value)

					if lang:
						self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
						# print("Reference added.")
					if qualifier_id and qualval_id:
						self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
						# print("Qualifier added.")

		except:
			print('Error in adding numeric value.')

		return 0

	def addCoordinates(self, prop_id='', prop_value='', lang='', qualifier_id='', qualval_id='', confirm='', overwrite='', append=''):
		""" Adds coordinates to Wikidata """

		print(self.page.title())

		if prop_value and '|' in prop_value:
			prop_value = prop_value.split('|')
			try:
				lat, lon, precision = calc_coord(prop_value)
			except:
				print('Something went wrong while adding coordinates.')
				return

		if precision <= 0.0:
			print('Incorrect precision value obtained')
			return

		self.page.get()
		if prop_id in self.page.claims:
			choice = ''
			if not append and not overwrite:
				choice = input('Property already exists. Select:\n\
					1 to skip\n\
					2 to over-write the existing property\n\
					3 to add another value to the property\n')

			if choice == '1':
				return

			elif choice == '2' or overwrite == 'y':
				self.page.removeClaims(self.page.claims[prop_id])
		
			elif choice > '3':
				print("Invalid choice.\n")
				return 1

		try:
			new_prop = pywikibot.Claim(repo, prop_id)
			coordinate = pywikibot.Coordinate(lat=lat, lon=lon, precision=precision, site=enwp,globe_item=globe_item)
			new_prop.setTarget(coordinate)

			if confirm.lower() == 'y':
				self.page.addClaim(new_prop, summary=u'Importing new coordinate')
				self.page = pywikibot.ItemPage(enwd, self.wd_value)

				if lang:
					self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
					# print("Reference added.")
				if qualifier_id and qualval_id:
					self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
					# print("Qualifier added.")

			else:
				# confirmation
				print(new_prop)
				text = input("Do you want to save this property? (y/n) ")
				if text == 'y':
					self.page.addClaim(new_prop, summary = u'Importing new coordinate')
					self.page = pywikibot.ItemPage(enwd, self.wd_value)

					if lang:
						self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
						# print("Reference added.")
					if qualifier_id and qualval_id:
						self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
						# print("Qualifier added.")

		except:
			print('Error in adding numeric value.')

	def addDate(self, prop_id='', date='', lang='', qualifier_id='', qualval_id='', confirm='', overwrite='', append=''):
		""" Adds numeric values to Wikidata """

		print(self.page.title())

		if date and not re.search(r'\d-\d-\d', date, re.IGNORECASE):
			date = date.split()
			try:
				if len(date) == 3:
					value = dateparser.parse(str(date[0])+' '+str(date[1])+' '+str(date[2]))
					date = str(value.year) + '-' + str(value.month) + '-' + str(value.day)
				elif len(date) == 2:
					value = dateparser.parse(str(date[0])+' '+str(date[1]))
					date = str(value.year) + '-' + str(value.month)
				elif len(date) == 1:
					value = dateparser.parse(str(date[0]))
					date = str(value.year)
			except:
				print('Error in extracting date.\n')
				return

		if date and date != '0-0-0':
			self.page.get()

			if prop_id in self.page.claims:
				choice = ''
				if not append and not overwrite:
					choice = input('Property already exists. Select:\n\
						1 to skip\n\
						2 to over-write the existing property\n\
						3 to add another value to the property\n')

				if choice == '1':
					return

				elif choice == '2' or overwrite == 'y':
					self.page.removeClaims(self.page.claims[prop_id])
			
				elif choice > '3':
					print("Invalid choice.\n")
					return 1

			now = datetime.datetime.now()

			check_ok = True
			if int(date.split('-')[0]) > now.year:
				check_ok = False
			try:
				if int(date.split('-')[0]) == now.year and int(date.split('-')[1]) > now.month:
					check_ok = False
			except:
				print("Invalid date.\n")
				pass

			if check_ok:
				try:
					new_prop = pywikibot.Claim(repo, prop_id)

					if len(date.split('-')) == 3:
						new_prop.setTarget(pywikibot.WbTime(year=int(date.split('-')[0]), month=int(date.split('-')[1]), day=int(date.split('-')[2])))
					elif len(date.split('-')) == 2:
						new_prop.setTarget(pywikibot.WbTime(year=int(date.split('-')[0]), month=int(date.split('-')[1])))
					elif len(date.split('-')) == 1:
						new_prop.setTarget(pywikibot.WbTime(year=int(date.split('-')[0])))

					if confirm.lower() == 'y':
						self.page.addClaim(new_prop, summary = u'Adding new date')
						self.page = pywikibot.ItemPage(enwd, self.wd_value)

						if lang:
							self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
							# print("Reference added.")
						if qualifier_id and qualval_id:
							self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
							# print("Qualifier added.")

					else:
						# confirmation
						print(new_prop)
						text = input("Do you want to save this property? (y/n) ")
						if text == 'y':
							self.page.addClaim(new_prop, summary = u'Adding new date')
							self.page = pywikibot.ItemPage(enwd, self.wd_value)

							if lang:
								self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
								# print("Reference added.")
							if qualifier_id and qualval_id:
								self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
								# print("Qualifier added.")

				except:
					print('Error in adding numeric value.\n')
		return 0


	def addIdentifiers(self, prop_id='', prop_value='', lang='', qualifier_id='', qualval_id='', confirm='', overwrite='', append=''):
		""" Adds numeric values to Wikidata """

		print(self.page.title())

		if not prop_value:
			print('Incorrect property value provided.\n')
			return 1

		self.page.get()
		if prop_id in self.page.claims:
			choice = ''
			if not append and not overwrite:
				choice = input('Property already exists. Select:\n\
					1 to skip\n\
					2 to over-write the existing property\n\
					3 to add another value to the property\n')

			if choice == '1':
				return

			elif choice == '2' or overwrite == 'y':
				self.page.removeClaims(self.page.claims[prop_id])
		
			elif choice > '3':
				print("Invalid choice.\n")
				return 1

		try:
			new_prop = pywikibot.Claim(repo, prop_id)
			# print('hello')
			new_prop.setTarget(prop_value)
			# print(val)

			if confirm.lower() == 'y':
				self.page.addClaim(new_prop, summary = u'Adding new identifier')
				self.page = pywikibot.ItemPage(enwd, self.wd_value)

				if lang:
					self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
					# print("Reference added.")
				if qualifier_id and qualval_id:
					self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
					# print("Qualifier added.")

			else:
				# confirmation
				print(new_prop)
				text = input("Do you want to save this property? (y/n) ")
				if text == 'y':
					self.page.addClaim(new_prop, summary = u'Adding new identifier')
					self.page = pywikibot.ItemPage(enwd, self.wd_value)

					if lang:
						self.addImportedFrom(repo=repo, claim=new_prop, lang=lang, status=1)
						# print("Reference added.")
					if qualifier_id and qualval_id:
						self.addQualifiers(repo=repo, claim=new_prop, qualifier_id=qualifier_id, qualval_id=qualval_id, status=1)
						# print("Qualifier added.")

		except:
			print('Error in adding identifier.')

		return 0

	def checkClaimExistence(self, claim=''):
		"""
		Checks if a claim exists in Wikidata already

		@param claim: property and it's value to which this associated with

		"""
		claim_prop = claim.getID()
		claim_target = claim.getTarget()

		wd_items = self.page.get()

		for props in wd_items['claims']:
			if props == claim_prop:
				try:
					item = wd_items['claims'][props]
					for value in item:
						try:
							value_qid = value.getTarget()
							if claim_target.title() == value_qid.title():
								return value
						except:
							pass
				except:
					print('Error in browsing through items.')

		choice = input('Property and value do not exist. Select:\n\
			1 to add it Wikidata\n\
			2 to skip\n')

		if choice == '1':
			self.page.addClaim(claim, summary = u'Adding new property')
			self.page = pywikibot.ItemPage(enwd, self.wd_value)
			return claim
		elif choice == '2':
			print('Skipping the addition of property and source.\n')
			return 0
		else:
			print('Invalid choice.\n')
			return 0

		return 0


	def addImportedFrom(self, repo=repo, prop_id='', prop_value='', claim='', lang='', status=0):
		"""
		Adds a reference/source

		@param repo:
		@param prop_id: ID of the property
		@param prop_val: ID of value associated with property
		@param claim: property and it's value to which this associates with
		@param lang: language of the wiki - must be a value from 'langs' dict
		@param status: decide whether to test for claim's existence or not
						(0 - method is called directly by user
						 1 - method is called indirectly by other methods which add a property to Wd)

		"""
		if prop_id and prop_value:
			try:
				new_prop_val = pywikibot.ItemPage(enwd, prop_value)
				claim = pywikibot.Claim(enwd, prop_id)	
				claim.setTarget(new_prop_val)
			except:
				print('Incorrect property id or value provided.\n')
				return 1

		if status == 0:
			claim = self.checkClaimExistence(claim)

		if repo and claim and lang and lang in langs.keys():
			importedfrom = pywikibot.Claim(repo, 'P143') #imported from
			importedwp = pywikibot.ItemPage(repo, langs[lang])
			importedfrom.setTarget(importedwp)
			claim.addSource(importedfrom, summary='Adding 1 reference: [[Property:P143]]')
			self.page = pywikibot.ItemPage(enwd, self.wd_value)
			print('Reference/Source added successfully.\n')

		return 0

	def addQualifiers(self, repo=repo, prop_id='', prop_value='', claim='', qualifier_id='', qualval='', qualval_id='', status=0):
		"""
		Adds a qualifier

		@param qualifier_id: ID of the qualifier
		@param qualval_id: ID of the qualifier's value

		@type of all (except repo and claim): string

		"""
		if prop_id and prop_value:
			try:
				new_prop_val = pywikibot.ItemPage(enwd, prop_value)
				claim = pywikibot.Claim(enwd, prop_id)	
				claim.setTarget(new_prop_val)
			except:
				print('Incorrect property id or value provided.\n')
				return 1

		if status == 0:
			claim = self.checkClaimExistence(claim)

		if qualval_id:
			qualifier_val = pywikibot.ItemPage(repo, qualval_id)
		elif qualval:
			qualifier_val = qualval

		if repo and claim and qualifier_id:
			qualifier = pywikibot.Claim(repo, qualifier_id)
			qualifier.setTarget(qualifier_val)
			claim.addQualifier(qualifier, summary='Adding 1 qualifier')
			self.page = pywikibot.ItemPage(enwd, self.wd_value)
			print('Qualifier added successfully.\n')

		return 0


def main():
	# page_name = input('Name of article: ')
	# page_name = 'Hallock-Bilunas Farmstead'
	wd_value = 'Q4115189'
# 	wp_page = ''
# 	wd_page = ''

	# # Test for Wikipedia page
	# try:
	# 	wp_page = WpPage(page_name)
	# 	print(wp_page.searchWpPage(props={'P50': ['J. K. Rowling'], 'P123': ['Bloomsbury']}))
	# 	print('\n')
	# except:
	# 	('Page does not exist.\n')
	# 	return 1

	# if wp_page:
		# wp_page.printWpContents()
		# print('\n')
	# 	info = wp_page.findInfobox()
	# 	for prop in info.keys():
	# 		print(str(prop) + ': ' + str(info[prop]))
	# 	print('\n')

	# Test for Wikidata page
	try:
		wd_page = WdPage(wd_value)
	except:
		("Page does not exist.\n")
		return 1

	if wd_page:
	# 	wd_page.printWdContents()
		wd_page.addWdProp(prop_id='P607', prop_value='Gaius Marius', lang='en', qualifier_id='P1013', qualval_id='Q139')
		# wd_page.addFiles(prop_id='P18', prop_value='image: Anarchy-symbol.svg', lang='fr')
		# wd_page.addCoordinates(prop_id='P625', prop_value=info['coordinates'])
		# wd_page.addNumeric(prop_id='P1104', prop_value=123)
		# wd_page.addMonolingualText(prop_id='P1451', prop_value='hello', text_language='en')
		# wd_page.addIdentifiers(prop_id='P1451', prop_value='hello')
	# 	wd_page.addImportedFrom(prop_id='P31', prop_value='Q5', lang='en')
	# 	wd_page.addQualifiers(prop_id='P31', prop_value='Q5', qualifier_id='P1013', qualval_id='Q139')
		# wd_page.addDate(prop_id='P577', date='2012-02-03', lang='fr')
		# wd_page.addDate(prop_id='P577', date=info['added'], lang='fr')


# 	return 0
	
if __name__ == "__main__":
	main()
