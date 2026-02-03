#
# ASFcsvFromHtml.py
#
# Starting with the HTML page (created by Andrew May) which lists the 
# contents of each issue of Astounding Science Fiction from July 1939
# through September 1960, this script creates a CSV file containing
# that data, while doing some cleanup in the process (e.g. creating)
# an "Authors" column that contains the real name of the authors of 
# stories written under pen names.
#
# The original source page is here:
# https://www.andrew-may.com/asf/list.htm
#
# Written in January 2026, this is a major refactoring of code 
# originally written in conjunction with ChatGPT in August and 
# September of 2025.
#
# Bruce Watkins
#

import ssl
import certifi
import urllib.request
from   bs4 import BeautifulSoup
import pandas as pd
import re

#-------------------------------------------------------------------
def file_from_url(url_path):

	# Avoid issues with web site certificates and pretend that 
	# we are a Chrome browser.
	context = ssl.create_default_context(cafile=certifi.where())
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

	# Try requesting the page from the server. If that fails, display 
	# an error message and exit.
	req = urllib.request.Request(url_path, headers=headers)

	try:
	    with urllib.request.urlopen(req, context=context) as response:
	        the_file = response.read()

	except urllib.error.HTTPError as e:
	    print(f"HTTP Error: {e.code} - {e.reason}")
	    raise SystemExit(1)

	return the_file

#### End of function file_from_url

#-------------------------------------------------------------------
def html_to_soup(html_path):
#
# Read the HTML file containing the list of issues and their
# stories, and return a BeautifulSoup object with the parsed
# HTML.
#
	html = file_from_url(html_path)
	soup = BeautifulSoup(html, "html.parser")

	return soup

#### End of function html_to_soup

#-------------------------------------------------------------------
def soup_to_dataframe(the_soup):
#
# Walk thru the lines of the html, creating a list of dictionary
# elements, each containing Year, Month, Title, Published-As-Author.
# Then use that list to create a pandas dataframe object and 
# return it.
#
	# Replace all the br tags with new line characters.
	for br in the_soup.find_all("br"):
	    br.replace_with("\n")

	# Split the html text into a list of individual lines.
	text  = the_soup.get_text()
	lines = text.splitlines()

	# Initialize for the loop that will walk thru the list of lines.
	records       = []
	current_issue = None
	months = [
	    "January","February","March","April","May","June",
	    "July","August","September","October","November","December"
	]

	line_num = 0
	num_stories = 0

	for line in lines:

		line_num += 1
		line = line.strip()

		if not line:
			continue

	    # Split this line into words. If there are just
	    # 2 words, see if they are a month name followed by 
	    # a year. If so set the current issue.
		is_issue_line = False

		words = line.split()
		if len(words) == 2:
		    if (words[0] in months) & (re.match(r"\d\d\d\d",words[1]) != None):
		        is_issue_line = True
		        current_issue = line
		        # print(f'current issue: [{line}]')
		        # print(f'  prev issue had {num_stories} stories')
		        num_stories = 0

		# Process lines that are not issue lines.
		if not is_issue_line:

		    # Try to match "Title (Author)"
		    m = re.match(r"^(.*)\(([^()]*)\)$", line)

		    if m:
		        title  = m.group(1).strip()
		        author = m.group(2).strip()
		    else:
		        print(f'could not match line number {line_num} [{line}], does not appear to be Title (Author)')
		        continue

		    # Split issue into month + year
		    if current_issue:
		        parts = current_issue.split()
		        if len(parts) == 2:
		            month, year = parts
		        else:
		            month, year = current_issue, ""
		    else:
		        month, year = "", ""

		    num_stories += 1
		    records.append({
		        "Year": year,
		        "Month": month,
		        "Title": title,
		        "Published_As": author
		    })

	story_dataframe = pd.DataFrame(records)

	return story_dataframe

#### End of function soup_to_dataframe

#-------------------------------------------------------------------
def last_first(name):
#
# Given a person's name in first last format, returns the name in
# last, first format. Takes into account suffixes (Jr, II, etc.)
# and particles (van, van der, etc.).
#

    name = name.strip()
    if not name:
        return name

    # Recognize suffixes like Jr., Sr., II, III
    suffix_re = re.compile(r'(?:,\s*|\s+)(Jr\.?|Sr\.?|II|III|IV|V)$', re.IGNORECASE)
    m = suffix_re.search(name)
    suffix = ""
    if m:
        suffix = m.group(1).strip()
        name = name[:m.start()].strip().rstrip(',')

    # If already "Last, First" keep it
    if ',' in name:
        last, rest = [p.strip() for p in name.split(',', 1)]
        result = f"{last}, {rest}" if rest else last
    else:
        tokens = name.split()
        if len(tokens) == 1:
            result = tokens[0]
        else:
            particles = {
                "van", "von", "de", "del", "di", "da", "la", "le", "du",
                "dos", "st", "st.", "ter", "van der", "van den", "de la"
            }
            two_word = ""
            if len(tokens) >= 3:
                last_two = (tokens[-2] + " " + tokens[-1]).lower()
                if last_two in particles:
                    two_word = last_two
            if two_word:
                last = tokens[-2] + " " + tokens[-1]
                first = " ".join(tokens[:-2])
            elif tokens[-2].lower() in particles:
                last = tokens[-2] + " " + tokens[-1]
                first = " ".join(tokens[:-2])
            else:
                last = tokens[-1]
                first = " ".join(tokens[:-1])
            result = f"{last}, {first}" if first else last

    if suffix:
        result = f"{result} {suffix}"

    result = " ".join(result.split())

    return result

#### End of function last_first

#-------------------------------------------------------------------
def normalize_author(name):
#
# Given an author's name, return that name transformed into
# last, first format. Also combine any spelling variants of names
# into a single version of that name, and also change pen names
# into the actual name of the author.
#
	norm_name = name
	norm_name = last_first(norm_name)
	norm_name = combine_spellings(norm_name)
	norm_name = process_pennames(norm_name)

	return norm_name

#### End of function normalize_author

#-------------------------------------------------------------------
def spell_lastfirst(name):

	new_name = name
	new_name = last_first(new_name)
	new_name = combine_spellings(new_name)
	return new_name

#### End of function author_lastfirst_spell

#-------------------------------------------------------------------
def combine_spellings(name):
#
#
#
	real_name = change_aliases(name, spell_map)
	return real_name

#### End of function combine_spellings

#-------------------------------------------------------------------
def process_pennames(name):
#
#
#
	real_name = change_aliases(name, pen_map)
	return real_name

#### End of function process_pennames

#-------------------------------------------------------------------
def change_aliases(author, namemap):
#
# Given an author's name and a dictionary (map) that matches names
# to alternative names (misspellings or pen names), return the "real" 
# name of the author that should be used in place of the pen name or 
# alternative spelling found in the map.
#
    for real_name, aliases in namemap.items():
        if any(alias.lower() in str(author).lower() for alias in aliases):
            return real_name

    return author  # if no match, keep the original name

##### End of function change_aliases

#-------------------------------------------------------------------
def csv_to_map(csv_path):

	dframe = read_df_from_csv(csv_path)
	themap = {}

	for index, row in dframe.iterrows():
		value_list = dframe.iloc[index, 1].split('|')
		themap[dframe.iloc[index, 0]] = [s.strip() for s in value_list]

	return themap

##### End of function csv_to_map

#-------------------------------------------------------------------
def write_csv(story_dataframe, file_name):
#
#
#
	story_dataframe.to_csv(file_name)

	print(f"CSV file created: {file_name}")

#### End of function write_csv

#-------------------------------------------------------------------
def read_df_from_csv(file_path, drop_index=False):
##
## Return a pandas dataframe, given the path to a CSV spreadsheet. 
##
	if drop_index:
		try:
			df_from_csv = pd.read_csv(file_path, index_col=0)
		except FileNotFoundError:
		    st.error(f"Error: The file '{file_path}' was not found.")
		    sys.exit()
	else:
		try:
			df_from_csv = pd.read_csv(file_path)
		except FileNotFoundError:
		    st.error(f"Error: The file '{file_path}' was not found.")
		    sys.exit()

	return df_from_csv

#### End of function read_df_from_csv

##==================================================================================
##                               M  A  I  N                                       ##
##==================================================================================

# Get the list of spelling variations and the list of pen names as dictionaries (maps).
spellings_path = 'https://brucewatkins.org/sciencefiction/data/spellings-Spelling.csv'
pennames_path  = 'https://brucewatkins.org/sciencefiction/data/pennames-PenNames.csv'
pen_map   = csv_to_map(pennames_path)
spell_map = csv_to_map(spellings_path)

# Read the html page and parse it with BeautifulSoup.
soup = html_to_soup('https://brucewatkins.org/sciencefiction/data/origpage.html')

# Walk through the lines in the soup object, and create a dataframe listing the stories.
stories = soup_to_dataframe(soup)

# Add an Author column in which multiple spellings have been eliminated,
# and pen names have been replaced with actual names, and 
stories["Author"]       = stories["Published_As"].apply(normalize_author)
stories["Published_As"] = stories["Published_As"].apply(spell_lastfirst)

# Write the result to a spreadsheet in CSV format.
write_csv(stories, 'goldenstories.csv')

