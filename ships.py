# File name: ships.py
# Retrieves information from the infoboxes for ships and imports to Wikidata

import re
import pywikibot
import dateparser
import datetime
import base_ops as base

enwd = pywikibot.Site('wikidata', 'wikidata')
repo = enwd.data_repository()

""" 
=========================
Properties to be imported
=========================
"""
prop_ids = {
	'image': 'P18',
	'namesake': 'P138',
	'builder': 'P176', # manufacturer
	'manufacturer': 'P176',
	'motto': 'P1451', # motto text
	'nickname': 'P1449', # nickname
	'country': 'P8047', # country of registry
}

propval_ids = {
	'ordered': 'Q566889',
	'laid down': 'Q14592615',
	'launched': 'Q596643',
	'commissioned': 'Q14475832',

}

# segragating properties to use appropriate methods while importing
wikibase_item = ['P138', 'P176', 'P8047']
# files, images, etc.
commons_media = ['P18']
# properties which ideally contain only one value
single_values = ['P176', 'P1451', 'P8047']

lang = 'en'


""" 
====================================
Extracting information from infobox 
====================================
"""
def valParser(found_items=''):
	""" 
	"Refines" the data to remove unwanted text 

	@param found_items: list of found values

	"""
	# print(found_items)
	items = list()
	for found_item in found_items:
		found_item = found_item.replace('\'', '')
		found_item = found_item.split('<br>')
		for item in found_item:
			item = re.sub(r'[\<].*?[\>]', '', item)
			item = re.sub(r'\<.*', '', item)
			# print(item)
			items.append(item)
		# print('\n')

	return items

def searchProp(text=''):
	"""
	Searches for all the properties in the infobox

	@params text: text of the Wp page
	@return value: list of values 

	"""
	if not text:
		print('No text is available.')
		return 1

	found_items = ''
	try:
		found_items = re.findall(r'\|\s*(Ship [\sA-Z_]{3,})\=\s*', text, re.IGNORECASE)
		if not found_items:
			found_items = re.findall(r'\|\s*([\sA-Z_]{3,})\=\s*', text, re.IGNORECASE)
		return found_items
	except:
		print('Error in retrieving information for author')

	return 0

def searchPropValue(text='', word=''):
	"""
	Searches for values of the properties from infobox

	@params text: text of the Wp page
	@params word: word whose corresponding value is to be searched for
	@return value: list of values 

	"""
	if not text:
		print('No text is available.')
		return 1

	try:
		found_items = ''
		found_items = re.findall(r'\|\s*%s\s*\=\s*{{coord\|(.*)}}' % word, text, re.IGNORECASE)

		if not found_items:
			found_items = re.findall(r'\|\s*%s\s*\=\s*([^\n\{\}\|\/]{1,}[\w\)]{1,})' % word, text, re.IGNORECASE)
		# print(found_items)

		if found_items:
			item_list = valParser(found_items=found_items)
			return item_list
	except:
		print('Error in retrieving information for %s' % word)

	return 0

def searchInfobox(text=''):
	"""
	Searches for information from the infobox

	@params text: text of the Wp page
	@return value (dict): list of values 

	"""
	# print(text)
	if not text:
		print('No text is present.\n')
		return None

	properties = searchProp(text=text)
	print('Found ' + str(len(properties)) + ' properties.\n')

	propval_pair = dict()
	for prop in properties:
		value = searchPropValue(text=text, word=prop)
		
		try:
			if len(value) == 1:
				propval_pair[str(prop)] = value[0]
			else:
				propval_pair[str(prop)] = value
		except:
			# print('No corresponding value for ' + str(prop) + ' exists. Skipping...')
			pass

	# for prop in propval_pair:
	# 	print(str(prop) + " : " + str(propval_pair[prop]))

	print('\n')

	return propval_pair


""" 
=======================
Adding info to Wikidata 
=======================
"""
def checkExistence(claim='', prop_id='', prop_value=''):
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

		elif prop_id == 'P793':
			wd_propval = item_value.title()
			if prop_value == wd_propval:
				return True

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

	# wd_page = base.WdPage(wd_value='Q4115189')

	# addition of source url
	import_url = 'https://en.wikipedia.org/w/index.php?title=%s&oldid=%s' % (wp_page.title.replace(' ', '_'), wp_page.latest_revision_id)

	""" import details into Wikidata """
	if prop_id in commons_media:
		# setting captions/media legend for images
		caption = ''
		for prop in prop_list.keys():
			if 'caption' in prop:
				caption = prop
				break
		if prop_id == 'P18' and caption:
			caption_string = str(prop_list[caption]).replace('[', '').replace(']', '')
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

	# import of significant events
	elif prop_id == 'P793':
		wd_page.addWdProp(prop_id='P793', prop_value=prop_value, lang=lang, source_id='P4656', sourceval=import_url, confirm='y', append='y')

	return 0

def addDateQualifier(wd_page='', prop_id='', prop_val='', qual_id='', date=''):
	""" 
	Adds date as a qualifier (Point of time)

	@param wd_page: Wd page where qualifier is to be added
	@param prop_id: property id of the claim
	@param prop_val: prop val (QID) of val whose qualifier is to be added
	@param qual_id: qualifier's property id
	@param date: qualifier's date

	"""

	# convert to appropriate format
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

		# check for previous existence of property-value pair in page
		for prop_claim in wd_page.page.claims:
			if prop_id == prop_claim:
				items = wd_page.page.claims[prop_claim]

				# checks for prop-val pairs in qualifiers
				for item in items:
					for qualifier in item.qualifiers:
						if qual_id == qualifier:
							qual_items = item.qualifiers[qualifier]
							for qual_item in qual_items:
								if checkExistence(claim=qual_item, prop_id=prop_id, prop_value=prop_val):
									print('Same property-value exist in the page as qualifier. Skipping...')
									return 1

		# checks validity of date
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
			for prop_claim in wd_page.page.claims:
				if prop_id == prop_claim:
					items = wd_page.page.claims[prop_claim]
					try:
						for item in items:
							if item.getTarget().title() == prop_val:
								qualifier = pywikibot.Claim(repo, qual_id)

								if len(date.split('-')) == 3:
									qualifier.setTarget(pywikibot.WbTime(year=int(date.split('-')[0]), month=int(date.split('-')[1]), day=int(date.split('-')[2])))
								elif len(date.split('-')) == 2:
									qualifier.setTarget(pywikibot.WbTime(year=int(date.split('-')[0]), month=int(date.split('-')[1])))
								elif len(date.split('-')) == 1:
									qualifier.setTarget(pywikibot.WbTime(year=int(date.split('-')[0])))

								item.addQualifier(qualifier, summary='Adding 1 qualifier')
								wd_page.page = pywikibot.ItemPage(enwd, wd_page.wd_value)
								print('Qualifier added successfully.\n')

					except:
						print('Error in adding date qualifier.\n')
	return 0

def main():
	article_name = 'INS Kochi'
	wp_page = base.WpPage(article_name)

	# check for existence of page
	if wp_page.getWpContents():
		# wp_page.printWpContents()
		print(wp_page.title)

		""" Extracting info from infobox and adding to Wikidata """
		# find info from the infobox
		info_box = list()
		text_screened = re.findall(r'\{\{Infobox .*[\n]*', wp_page.page.text, re.DOTALL)
		if text_screened:
			text = text_screened[0].split('==')
			text = text[0].rsplit('\n}}')

			for txt in text:
				if re.search(r'{{Infobox', txt, re.IGNORECASE):
					res = searchInfobox(text=txt)
					if res:
						info_box.append(res)

		# get the Wd page
		wd_page = ''
		try:
			wd_page = base.WdPage(page_name=wp_page.title)
		except:
			pass

		# wd_page = base.WdPage(wd_value='Q4115189')

		if info_box and wd_page:
			# iterate through each info extracted from infobox
			# print(info_box)

			for info in info_box:
				for prop in info.keys():
					wdprop = prop
					if re.search(r'Ship\s*[\w]+', prop, re.IGNORECASE):
						wdprop = re.sub(r'Ship\s*', '', prop, flags=re.IGNORECASE)
					wdprop = wdprop.strip()
					print(str(wdprop) + ': ' + str(info[prop]))
					if wdprop in prop_ids:
						try:
							# multiple values for a prop - add each value separately
							if type(info[prop]) is list:
								for val in info[prop]:
									try:
										addToWd(wp_page=wp_page, wd_page=wd_page, prop_id=prop_ids[str(wdprop)], prop_value=val, prop_list=info)
									except:
										print('Error adding property.')
										continue
							else:
								addToWd(wp_page=wp_page, wd_page=wd_page, prop_id= prop_ids[str(wdprop)], prop_value=info[prop], prop_list=info)

							print('\n')
						except:
							pass
					elif wdprop in propval_ids:
						try:
							significant_event = addToWd(wp_page=wp_page, wd_page=wd_page, prop_id='P793', prop_value=propval_ids[wdprop])
							# wd_page = base.WdPage(wd_value='Q4115189')
							if not significant_event:
								addDateQualifier(wd_page=wd_page, prop_id='P793', prop_val=propval_ids[wdprop], qual_id='P585', date=info[prop])
						except:
							print('Error adding significant event.')


	else:
		print('No such page exists. Skipping...\n')

if __name__ == "__main__":
	main()
