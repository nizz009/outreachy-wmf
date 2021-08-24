# File name: historicplaces_browncounty_wisconsin.py
# https://en.wikipedia.org/wiki/National_Register_of_Historic_Places_listings_in_Brown_County,_Wisconsin

import re
import pywikibot
import dateparser
import time
import urllib
import urllib.request
import urllib.parse
import base_ops as base
import search_patterns

# properties to be imported
prop_ids = {
	'image': 'P18',
	'county': 'P131',
	'coordinates': 'P625',
	'refnum': 'P649',
}

# segragating properties to use appropriate methods while importing
wikibase_item = ['P131']
# files, images, etc.
commons_media = ['P18']
coordinates = ['P625']
identifier = ['P649']
# properties which ideally contain only one value
single_values = ['P131', 'P625', 'P649']

lang = 'en'
enwd = pywikibot.Site("wikidata", "wikidata")
repo = enwd.data_repository()


""" 
=====================================
Searching and creating Wikidata Items
=====================================
"""
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

def searchWdPage(article_name=''):
	""" Searches for a Wp article in Wd """ 

	article_name_ = article_name.split('(')[0].strip()
	searchitemurl = 'https://www.wikidata.org/w/api.php?action=wbsearchentities&search=%s&language=en&format=xml' % (urllib.parse.quote(article_name_))
	raw = getURL(searchitemurl)

	if not '<search />' in raw:
		return 1

	return None

# reference: https://bitbucket.org/mikepeel/wikicode/src/master/enwp_wikidata_newitem.py
def createWdPage(article_name=''):
	""" Creates a new Wikidata Page """

	new_item = pywikibot.ItemPage(repo)
	new_item.editLabels(labels={"en":article_name}, summary="Creating item")
	return new_item.getID()


""" 
==============================
Adding information to Wikidata  
==============================
"""
def checkExistence(claim='', prop_id='', prop_value='',):
	""" 
	Checks for the existence of a claim with the given

	@param claim: the claim to be compared with
	@param prop_id: property ID of the property to be added/checked
	@param prop_value: value of property to be looked for

	"""
	try:
		item_value = claim.getTarget()
		
		if prop_id in commons_media:
			wd_propval = item_value.title()
			wd_propval = wd_propval.replace('File:', '').replace('Image:', '').replace('image:', '').lower()
			article_file = prop_value.replace('File:', '').replace('Image:', '').replace('image:', '').lower()
			if article_file == wd_propval:
				return True

		elif prop_id in wikibase_item:
			wd_propval = item_value.title()
			wdpage_val = base.WdPage(wd_value=wd_propval)
			wdpage_value = wdpage_val.page.labels['en'].lower()
			prop_value_refined = prop_value.replace('[', '').replace(']', '')
			if prop_value_refined.lower() == wdpage_value:
				return True

		elif prop_id in coordinates:
			if prop_value and '|' in prop_value:
				coord_value = prop_value.split('|')
				try:
					lat, lon, precision = base.calc_coord(coord_value)
				except:
					print('Something went wrong while adding coordinates.')
					return 1

			if precision > 0 and lat == item_value.lat and lon == item_value.lon and precision == item_value.precision:
				print('Same property-value exist in the page already. Skipping...')
				return 1

		elif prop_id in identifier:
			if prop_value == item_value:
				print('Same property-value exist in the page already. Skipping...')
				return 1	
	except:
		pass

	return False

def addToWd(wp_page='', wd_page='', prop_id='', prop_value='', prop_list=''):
	""" Adds info to Wikidata """

	# check for previous existence of property-value pair in page
	for prop_claim in wd_page.page.claims:
		items = wd_page.page.claims[prop_claim]

		if prop_id == prop_claim:
			if prop_id in single_values:
				print('The property exists already. Skipping...')
				return

			for item in items:
				if checkExistence(claim=item, prop_id=prop_id, prop_value=prop_value):
					print('Same property-value exist in the page already. Skipping...')
					return 1

		# checks for prop-val pairs in qualifiers
		for item in items:
			for qualifier in item.qualifiers:
				if prop_id == qualifier:
					qual_items = item.qualifiers[qualifier]
					for qual_item in qual_items:
						if checkExistence(claim=qual_item, prop_id=prop_id, prop_value=prop_value):
							print('Same property-value exist in the page as qualifier. Skipping...')
							return 1

	wd_page = base.WdPage(wd_value='Q4115189')

	# addition of source url
	import_url = 'https://en.wikipedia.org/w/index.php?title=%s&oldid=%s' % (wp_page.title.replace(' ', '_'), wp_page.latest_revision_id)

	""" import details into Wikidata """
	if prop_id in commons_media:
		# setting captions/media legend for images
		if prop_id == 'P18' and 'caption' in prop_list.keys():
			caption_string = str(prop_list['caption']).replace('[', '').replace(']', '')
			caption = pywikibot.WbMonolingualText(text=caption_string, language=lang)
			wd_page.addFiles(prop_id=prop_id, prop_value=prop_value, lang=lang, source_id='P4656', sourceval=import_url, qualifier_id='P2096', qualval=caption, confirm='y', append='y')
		else:
			wd_page.addFiles(prop_id=prop_id, prop_value=prop_value, lang=lang, source_id='P4656', sourceval=import_url, confirm='y', append='y')

	elif prop_id in wikibase_item:
		# check for string or link to Wp article ('[[<Wp article name>')
		if '[' not in prop_value:
			print('Simple string present. Skipping...')
			return 1

		try:
			partition = '[['
			if partition in prop_value:
				prop_value = prop_value.partition(partition)[2]
			prop_value = prop_value.replace('[', '').replace(']', '')
			value_wp_page = base.WpPage(prop_value.strip())
			value_wd_page = base.WdPage(page_name=value_wp_page.title)
			wd_page.addWdProp(prop_id=prop_id, prop_value=value_wd_page.wd_value, lang=lang, source_id='P4656', sourceval=import_url, confirm='y', append='y')

		except:
			print('Error adding new wd property.')

	elif prop_id in coordinates:
		wd_page.addCoordinates(prop_id=prop_id, prop_value=prop_value, lang=lang, source_id='P4656', sourceval=import_url, confirm='y', append='y')

	elif prop_id in identifier:
		wd_page.addIdentifiers(prop_id=prop_id, prop_value=prop_value, lang=lang, source_id='P4656', sourceval=import_url, confirm='y', append='y')

	return 0

def main():
	page_name = 'National Register of Historic Places listings in Brown County, Wisconsin'

	wp_list = base.WpPage(page_name)
	# wp_list.printWpContents()

	""" Retrieving names of the Wp articles """
	contents = wp_list.getWpContents()
	list_items = re.split(r'==[\w\s]*==', contents)[1]
	indiv_items = re.split(r'{{NRHP row', list_items)

	for item in indiv_items:
		# print(item)
		article_name = re.findall(r'\|article\=(.+)', item)
		if not article_name:
			continue
		wp_page = base.WpPage(article_name[0])
		# print(article_name)

		if wp_page.getWpContents():
				print(wp_page.title)

		# get the Wd page
		wd_page = ''
		try:
			wd_page = base.WdPage(page_name=wp_page.title)
		except:
			print('no wd page exists.\n')
			pass
		
		# creates new Wikidata Item 
		if not wd_page:
			wdpage_exists = searchWdPage(article_name=article_name[0])
			if not wdpage_exists:
				new_wdvalue = createWdPage(article_name=article_name[0])
				wd_page = base.WdPage(new_wdvalue)

		# wd_page = base.WdPage(wd_value='Q4115189')

		if wd_page:
			properties = search_patterns.search_prop(item)
			for prop in properties:
				print(prop)
				if prop in prop_ids:
					prop_val = search_patterns.search_prop_value(page_text=item, word=prop)
					print(str(prop) + ': ' + str(prop_val))
					try:
						# multiple values for a prop - add each value separately
						if type(prop_val) is list:
							for val in prop_val:
								try:
									addToWd(wp_page=wp_page, wd_page=wd_page, prop_id=prop_ids[str(prop)], prop_value=val, prop_list=properties)
								except:
									print('Error adding property.')
									continue

						print('\n')
					except:
						pass

				if prop == 'lat':
					lat = search_patterns.search_prop_value(page_text=item, word=properties[properties.index('lat')])[0]
					lon = search_patterns.search_prop_value(page_text=item, word=properties[properties.index('lon')])[0]
					val = str(lat) + '|' + str(lon)
					addToWd(wp_page=wp_page, wd_page=wd_page, prop_id=prop_ids['coordinates'], prop_value=val, prop_list=properties)

			else:
				print('No such page exists. Skipping...\n')
				continue

				# if i < 25:
				# 	i += 1
				# else:
				# 	break

if __name__ == "__main__":
	main()
