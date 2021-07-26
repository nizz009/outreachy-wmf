# File name: guerrilla_movements.py
# https://en.wikipedia.org/wiki/List_of_guerrilla_movements

import re
import pywikibot
import datetime
import dateparser
import base_ops as base

# properties to be imported
prop_ids = {
	'country': 'P17',
	'image': 'P18',
	'leaders': 'P35',
	'flag': 'P41',
	'logo': 'P154',
	'garrison': 'P159',
	'headquarters': 'P159',
	'founded': 'P571', # date
	'battles': 'P607',
	'conflict': 'P607',
	'allegiance': 'P945',
	'predecessor': 'P1365',
	'motto': 'P1451',
	'motive': 'P1451',
	'native_name': 'P1705',
	'abbreviation': 'P1813',
	'caption': 'P2096',
	'general_secretary': 'P3975',
	'youth_wing': 'P4379',
	'other_name': 'P4970',
	'opponents': 'P7047',
	'enemy': 'P7047',
	'merger': 'P7888',
}

# segragating properties to use appropriate methods while importing
wikibase_item = ['P17', 'P35', 'P159', 'P407', 'P607', 'P945', 'P1365', 
				'P3975', 'P4379', 'P7047', 'P7888']
# files, images, etc.
commons_media = ['P18', 'P41', 'P154']
# dates, etc.
time = ['P571']
# monolingual text
string = ['P1451', 'P1705', 'P1813']
# properties which ideally contain only one value
single_values = ['P17', 'P159', 'P571', 'P945', 'P1365', 'P7888']

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

	return 0

def main():
	page_name = 'List of guerrilla movements'

	wp_list = base.WpPage(page_name)
	# wp_list.printWpContents()

	contents = wp_list.getWpContents()
	list_items = re.split(r'==[\w\s]*==', contents)
	# print(list_items)

	""" Extracting names of the Wp articles """
	items = list()
	for i in range(1, 22):
		items.append(list_items[i])

	i = 0
	rows = list()
	for item in items:
		# print(item)
		rows = item.split('*')

		for row in rows:
			# print(row)
			if '[[' in row:
				if '[[File:' in row:
					movement = re.findall(r'\[\[(.*?)\]\]', row)[1]
				else:
					movement = re.findall(r'\[\[(.*?)\]\]', row)[0]

				if '|' in movement:
					movement = movement.split('|')[0]

				wp_page = base.WpPage(movement)
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
