# File name: historicplaces_riverhead_ny.py
# https://en.wikipedia.org/wiki/National_Register_of_Historic_Places_listings_in_Riverhead_(town),_New_York

import re
import pywikibot
import dateparser
import base_ops as base

# properties to be imported
prop_ids = {
	'image': 'P18',
	'architecture': 'P149',
	'location': 'P279',
	'built': 'P571',
	'coordinates': 'P625',
	'refnum': 'P649',
	'caption': 'P2096',
}

# segragating properties to use appropriate methods while importing
wikibase_item = ['P149', 'P279']
# files, images, etc.
commons_media = ['P18']
# dates, etc.
time = ['P571']
# monolingual text
string = ['P1451', 'P1705', 'P1813']
coordinates = ['P625']
identifier = ['P649']
# properties which ideally contain only one value
single_values = ['P149', 'P571', 'P625', 'P649']

lang = 'en'

def addToWd(wd_page='', prop_id='', prop_value='', prop_list=''):

	""" check for previous existence of property-value pair in page """
	if prop_id in wd_page.page.claims:
		if prop_id in single_values:
			print('The property exists already. Skipping...')
			return

		item = wd_page.page.claims[prop_id]
		# iterates through each value associated with each prop id
		for value in item:
			# print(value)
			try:
				item_value = value.getTarget()
				if prop_id in time:
					flag = 0
					date = prop_value.split()
					try:
						if len(date) == 3:
							import_date = dateparser.parse(str(date[0])+' '+str(date[1])+' '+str(date[2]))
							if import_date.year == item_value.year and import_date.month == item_value.month and import_date.day == item_value.day:
								flag = 1
						elif len(date) == 2:
							import_date = dateparser.parse(str(date[0])+' '+str(date[1]))
							if import_date.year == item_value.year and import_date.month == item_value.month:
								flag = 1
						elif len(date) == 1:
							import_date = dateparser.parse(str(date[0]))
							if import_date.year == item_value.year:
								flag = 1
					except:
						print('Error in extracting date.\n')
						return
					if flag:
						print('Same property-value exist in the page already. Skipping...')
						return 1
					
				elif prop_id in commons_media:
					wd_propval = item_value.title()
					wd_propval = wd_propval.strip('File:').strip('Image:').strip('image:').lower()
					prop_value = prop_value.strip('File:').strip('Image:').strip('image:').lower()
					if prop_value == wd_propval:
						print('Same property-value exist in the page already. Skipping...')
						return 1

				elif prop_id in string:
					if prop_value == item_value.text:
						print('Same property-value exist in the page already. Skipping...')
						return 1

				elif prop_id in wikibase_item:
					wd_propval = item_value.title()
					wdpage_val = base.WdPage(wd_value=wd_propval)
					wdpage_value = wdpage_val.page.labels['en'].lower()
					if prop_value.lower() == wdpage_value:
						print('Same property-value exist in the page already. Skipping...')
						return 1

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

	# wd_page = base.WdPage(wd_value='Q4115189')
	
	""" import details into Wikidata """
	if prop_id in time:
		wd_page.addDate(prop_id=prop_id, date=prop_value, lang=lang, confirm='y', append='y')
		
	elif prop_id in commons_media:
		# setting captions/media legend for images
		if prop_id == 'P18' and 'caption' in prop_list.keys():
			caption = pywikibot.WbMonolingualText(text=str(prop_list['caption']), language=lang)
			wd_page.addFiles(prop_id=prop_id, prop_value=prop_value, lang=lang, qualifier_id='P2096', qualval=caption, confirm='y', append='y')
		else:
			wd_page.addFiles(prop_id=prop_id, prop_value=prop_value, lang=lang, confirm='y', append='y')

	elif prop_id in string:
		if 'native_name_lang' in prop_list.keys():
			wd_page.addMonolingualText(prop_id=prop_id, prop_value=prop_value, lang=lang, text_language=str(prop_list['native_name_lang']), confirm='y', append='y')
		else:
			print('Missing native language.')

	elif prop_id in wikibase_item:
		wd_page.addWdProp(prop_id=prop_id, prop_value=prop_value, lang=lang, confirm='y', append='y')

	elif prop_id in coordinates:
		wd_page.addCoordinates(prop_id=prop_id, prop_value=prop_value, lang=lang, confirm='y', append='y')

	elif prop_id in identifier:
		wd_page.addIdentifiers(prop_id=prop_id, prop_value=prop_value, lang=lang, confirm='y', append='y')

	return 0

def main():
	page_name = 'National Register of Historic Places listings in Riverhead (town), New York'

	wp_list = base.WpPage(page_name)
	# wp_list.printWpContents()

	""" Retrieving names of the Wp articles """
	contents = wp_list.getWpContents()
	list_items = re.split(r'==[\w\s]*==', contents)[1]

	article_names = re.findall(r'\|article\=(.+)', list_items)

	# i = 0
	rows = list()
	for article_name in article_names:
		wp_page = base.WpPage(article_name)

		# check for existence of page
		if wp_page.getWpContents():
			print(wp_page.title)

			""" Extracting info from infobox and adding to Wikidata """
			# find info from the infobox
			info = wp_page.findInfobox(check_all='y')

			# get the Wd page
			wd_page = ''
			try:
				wd_page = base.WdPage(page_name=wp_page.title)
			except:
				pass

			# wd_page = base.WdPage(wd_value='Q4115189')

			if info and wd_page:
				# iterate through each info extracted from infobox
				for prop in info.keys():
					print(str(prop) + ': ' + str(info[prop]))
					try:
						# multiple values for a prop - add each value separately
						if type(info[prop]) is list:
							for val in info[prop]:
								try:
									addToWd(wd_page=wd_page, prop_id=prop_ids[str(prop)], prop_value=val, prop_list=info)
								except:
									print('Error adding property.')
									continue
						else:
							addToWd(wd_page=wd_page, prop_id= prop_ids[str(prop)], prop_value=info[prop], prop_list=info)

						print('\n')
					except:
						pass

		else:
			print('No such page exists. Skipping...\n')
			continue

		# if i < 25:
		# 	i += 1
		# else:
		# 	break

if __name__ == "__main__":
	main()
