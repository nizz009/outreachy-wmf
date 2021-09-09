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
	'codename': 'P1638',
}

# monolingual text
string = ['P1638']
# properties which ideally contain only one value
single_values = ['P1638']

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

	# new_item = pywikibot.ItemPage(repo)
	# new_item.editLabels(labels={"en":article_name}, summary="Creating item")
	# return new_item.getID()

	return 0


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
		
		if prop_id in string:
			prop_value = prop_value.replace('[', '').replace(']', '')
			if prop_value == item_value.text:
				return True	
	except:
		pass

	return False

def addToWd(wp_page='', wd_page='', prop_id='', prop_value='', prop_list='', import_url=''):
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

	""" import details into Wikidata """
	if prop_id in string:
		wd_page.addMonolingualText(prop_id=prop_id, prop_value=prop_value, lang=lang, source_id='P4656', sourceval=import_url, text_language=lang, confirm='y', append='y')

	return 0

def main():
	page_name = 'List of Microsoft codenames'

	wp_list = base.WpPage(page_name)
	# wp_list.printWpContents()

	""" Retrieving names of the Wp articles """
	contents = wp_list.getWpContents()
	# wp_list.printWpContents()
	list_items = re.split(r'==[\w\s]*==', contents)
	for list_item in list_items:
		version = re.split(r'\|-', list_item)
		for v in version:
			indiv_items = re.split(r'\|', v)
			article_name = ''
			try:
				if indiv_items[1] and indiv_items[3]:
					article_name = indiv_items[3].strip('[[')
					article_name = article_name.strip(']]\n')
			except:
				pass

			if not article_name:
				continue
			wp_page = base.WpPage(article_name)
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
					wdpage_exists = searchWdPage(article_name=article_name)
					if not wdpage_exists:
						new_wdvalue = createWdPage(article_name=article_name)
						wd_page = base.WdPage(new_wdvalue)

				# wd_page = base.WdPage(wd_value='Q4115189')

				if wd_page:
					try:
						# addition of source url
						import_url = 'https://en.wikipedia.org/w/index.php?title=%s&oldid=%s' % (wp_page.title.replace(' ', '_'), wp_list.latest_revision_id)
						addToWd(wp_page=wp_page, wd_page=wd_page, prop_id=prop_ids['codename'], prop_value=indiv_items[1].strip('[[').strip(']]\n'), import_url=import_url)
					except:
						print('Error adding property.')
						continue

				else:
					print('No such page exists. Skipping...\n')
					continue

if __name__ == "__main__":
	main()
