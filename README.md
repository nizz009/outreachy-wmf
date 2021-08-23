# outreachy-wmf
Scripts specifically for Outreachy Round 22 project in Wikimedia Foundation (WMF) - Synchronising Wikidata and Wikipedias using pywikibot

(N.B. Clone [nizz009/pywikibot](https://github.com/nizz009/pywikibot) repository for test runs)

## File Info (& Notes):

### Basic Operations

#### base_ops.py
Contains basic operations/resuable code for working with Wikipedia and Wikidata pages.

#### search_patterns.py
Extracts information from the Wikipedia articles

##### [Recti/Modi]fications:
1. Improvise searching of the infobox

### Categories

#### import_soccerway_id.py (approved)
Adds the missing soccerway ids in Wd whose Wp pages use the socceryway id template <br>
Follows the following layout:
1. No IDs - get their ID
2. With IDs - check authenticity
	1. Correct - add to Wd
	2. Incorrect - get their ID

### Lists
Iterates through the Wikipedia articles/pages mentioned in the lists and imports information from the infoboxes of each article/page - also adds the P143 reference

#### 1. guerrilla_movements.py
#### 2. list_folk_heroes.py
#### 3. historicplaces_riverhead_ny.py

## Things to work on:

1. Categories
2. Lists
3. Templates