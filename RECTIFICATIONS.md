## [Recti/Modi]fications:

### Lists
#### Error: 
Import of WikibaseItem

#### Description:
The string value is compared and import which results in errors.

#### Fix:
* Extract information only from `[[...]]` (or the first part after splitting `[[...|...]]` on basis of '|')
* Get Wp page from value dervied from above
* Get Wd page using Wp page (removes the previous error of getting the wrong Wd page when multiple Wd pages with same name existed)
* Get the title and add it

#### New error:
Where to add it for a cleaner and reusable code?
##### Possible solutions (not really) 
1. Modify seach_patterns.py to segragate the incoming properties - not reusable for all the articles
2. Extract info from infobox for all articles in the script itself - destroys the purpose of search_patterns.py
3. Do not replace `[[]]` and check for this in the script for the list - must be present for WikibaseItem, (else skip) and then extract the info from the sq. brackets (Seems viable)
