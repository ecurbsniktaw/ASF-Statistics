#===============================================================
#
# Data Analysis for the content of Astounding Science Fiction
# magazine from July 1939 to September 1960.
#
# The data used here was extracted from this web page:
#  https://www.andrew-may.com/asf/list.htm
# which was created by Andrew May:
#  https://www.andrew-may.com/bio.htm
#
# Written by Bruce Watkins (with help from chatgpt), 2025/2026
#
#===============================================================

import streamlit               as st
import pandas                  as pd
import streamlit.components.v1 as components
import matplotlib.pyplot       as plt
from   matplotlib.backends.backend_pdf import PdfPages
import matplotlib.ticker       as ticker
import io
import sys

#-------------------------------------------------------------------
def list_to_table(heading_list, rows_list):
##
## Generate and return the text of an HTML table.
##
## rows_list:    a list of lists with the values for the rows,
## heading_list: text for the table headings.
##
	html_text = [
	'<table id="interact" class="display" style="width:100%"> ',
	' <thead>',
	'  <tr>'
	]

	for head in heading_list:
		html_text.append(f'  <th>{head}</th>')

	html_text.append(' </tr>')
	html_text.append('</thead>')

	html_text.append(' <tbody>')

	for this_row in rows_list:
		# st.write(this_row)
		html_text.append(' <tr>')
		for this_col in this_row:
			html_text.append(f'  <td>{this_col}</td>')
		html_text.append(' </tr>')

	html_text.append(' </tbody>')
	html_text.append('</table>')

	return "\n".join(html_text)

### End of function list_to_table

#-------------------------------------------------------------------
def author_pivot():
##
## Return a pandas dataframe containing the number of stories by
## each author for each year. Assumes that the table of all
## stories has already been read into a global dataframe
## named df_all_stories.
##
	author_year_pivot = pd.pivot_table(
	    df_all_stories,
	    index="Author",
	    columns="Year",
	    values="Title",     # counting stories
	    aggfunc="count",
	    fill_value=0        # if no stories that year, put 0
	)
	author_year_pivot["Total"] = author_year_pivot.sum(axis=1)
	author_year_pivot = author_year_pivot.reset_index()

	return author_year_pivot

#### End of function author_pivot

#-------------------------------------------------------------------
def show_data_table(panda_df, heading_list, widthCol, widthVal):
##
## Displays an HTML table, using the datatables css/javascript package  
## so that the table is interactive: able to be sorted, searched, and 
## filtered.
##
## panda_df:     a pandas dataframe, 
## heading_list: heading titles, 
## sortCol:      column number to be sorted,
## sortHow:      sort direction, 
## widthCol:     column number to be forced to a specific width,
## widthVal:     width of that column.
##
	data_table_links = """
	<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/2.3.5/css/dataTables.dataTables.css">
	<script type="text/javascript" src="https://code.jquery.com/jquery-3.7.1.js"></script>
	<script type="text/javascript" src="https://cdn.datatables.net/2.3.5/js/dataTables.js"></script>
	"""
	data_table_script = f"""
		<script>
		let table = new DataTable
		(
		'#interact', 
		{{
		 "autoWidth": false,
		 "order": [],
	     columnDefs: [ {{ targets: {widthCol}, width: '{widthVal}' }}]
		}}
		);

		table.on('click', 'tbody tr', function () 
		{{
		    //let data = table.row(this).data();
		    //alert('You clicked on ' + data[0] + "'s row");
		}}

		);

		</script>
	"""
	list_of_rows = panda_df.to_numpy().tolist()
	html_table   = list_to_table(heading_list, list_of_rows)
	the_html     = data_table_links + html_table + data_table_script
	components.html(the_html, height=2000, width=1500, scrolling=True)

#### End of function show_data_table

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

#-------------------------------------------------------------------
def show_dl_button(kind, object, btn_label, file_name):
##
## Display a button for downloading either a pdf file or a
## CSV spreadsheet.
##	
	match kind:

		case 'pdf':
			mime_type = 'application/pdf'

		case 'csv':
			mime_type = 'text/csv'

	with st.sidebar:
		st.download_button(
		    label=btn_label,
		    data=object,
		    file_name=file_name,
		    mime=mime_type
		)

#### End of function show_dl_button

#-------------------------------------------------------------------
def show_multiline_plot_with_dl(index_list, value_lists, authors, title):
##
## Display a line plot of stories by year for multiple authors.
##
## index_list:	Lists of x values, e.g. years.
## value_lists:	A list of lists, each of which has y values, e.g.
##				number of stories published that year by this
##				author.
## authors:		List of author names.
##
	fig, ax = plt.subplots()

	for ndx, value_list in enumerate(value_lists):
		dataframe = pd.DataFrame(
		    {
		        f"{authors[ndx]}": value_list
		    },
		    index=index_list,
		)
		ax = dataframe.plot(kind='line', ax=ax, marker='.', title=title, grid=True)

	ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
	ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
	ax.spines['bottom'].set_position(('data', 0))

	plt.tight_layout()
	st.set_page_config(layout="centered")
	st.pyplot(fig)

	# Save the plot to a BytesIO object as PDF
	pdf_buffer = io.BytesIO()
	plt.savefig(pdf_buffer, format="pdf", bbox_inches="tight")
	pdf_buffer.seek(0)

	show_dl_button('pdf', pdf_buffer, 'Download PDF', 'multiplot.pdf')

	plt.close()

#### End of function show_multiline_plot_with_dl

#-------------------------------------------------------------------
def show_plot_with_dl_button(dataframe, which_type, title):
##
## Display a line plot of stories by year for a single author.
##
## dataframe:	contains the data to be plotted
## which_type:	'bar' chart or 'line' plot or 'barh' horiz. bar
## title:		title for the generated plot
##
	fig, ax = plt.subplots()

	match which_type:

		case 'bar':
			dataframe.plot(kind=which_type, stacked=True, ax=ax, title=title, grid=True)

		case 'line':
			ax = dataframe.plot(kind=which_type, ax=ax, marker='.', title=title, grid=True)
			ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
			ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
			ax.spines['bottom'].set_position(('data', 0))

		case 'barh':
			if len(dataframe) > 20:
				fig.set_size_inches(8, 8)
			ax = dataframe.plot.barh(legend=False)
			ax.invert_yaxis()
			plt.grid(color='black', linestyle=':', linewidth=1.0, axis='x', alpha=0.6)
			plt.title(title)
			plt.xlabel('Number of Stories')
			plt.ylabel('')

	plt.tight_layout()
	st.set_page_config(layout="centered")
	st.pyplot(fig)

	# Save the plot to a BytesIO object as PDF
	pdf_buffer = io.BytesIO()
	plt.savefig(pdf_buffer, format="pdf", bbox_inches="tight")
	pdf_buffer.seek(0)

	with st.sidebar:
		show_dl_button('pdf', pdf_buffer, 'Download as PDF', 'matplotlib_plot.pdf')

	# Close the Matplotlib figure to free up memory
	plt.close()

#### End of function show_plot_with_dl_button

#-------------------------------------------------------------------
def show_csv_dl_button(df, dl_file_name):
##
## Display a button for downloadig a table as a CSV spreadsheet.
##
	# Create a csv version of the data.
	csv = df.to_csv(index=False).encode('utf-8')

	# Provide a download button.
	with st.sidebar:
		st.download_button(
		    label="Download as CSV",	# The text on the button
		    data=csv, 					# The data to be downloaded
		    file_name=dl_file_name, 	# The default file name
		    mime='text/csv', 			# The MIME type for CSV files
	)

#### End of function show_csv_dl_button

#-------------------------------------------------------------------
def show_full_listing():
##
## Display a table listing all stories.
##
	title = f"""
	<h5>Stories Published in Astounding Science Fiction: July 1939 to September 1960</h5>
	"""
	st.markdown(title, unsafe_allow_html=True)

	st.set_page_config(layout="wide")
	heading_list = ['Seq', 'Year', 'Month', 'Title', 'Pub As', 'Author']
	show_data_table(df_all_stories, heading_list,'1', '25px')

	show_csv_dl_button(df_all_stories, 'allStories.csv')

#### End of function show_full_listing

#-------------------------------------------------------------------
def show_author_totals():
##
## Display total number of stories by each author, sorted by largest
## number of published stories first.
##
	author_counts = df_all_stories.groupby("Author").size().reset_index(name="StoryCount")
	author_counts.sort_values(by='StoryCount', ascending=False, inplace=True)

	title = f"""
	<h5>Total Number of Stories Published by Each Author</h5>
	"""
	st.markdown(title, unsafe_allow_html=True)

	st.set_page_config(layout="centered")
	heading_list = ['Author', 'Story Count']
	show_data_table(author_counts, heading_list, '0', '25%')

	show_csv_dl_button(author_counts, 'authorTotals.csv')

#### End of function show_author_totals

#-------------------------------------------------------------------
def show_author_by_year():
##
## Display table of stories by each author for each year, with
## total stories for each author over all years.
##
	author_year_pivot = author_pivot()

	# Move the totals to column 2, so you don't have to scroll to the right to see it.
	new_heads = ['Author', 'Total', 1939, 
			1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 1948, 1949, 
			1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 
			1960] 
	author_year_pivot = author_year_pivot[new_heads]
	author_year_pivot = author_year_pivot.sort_values(by='Total', ascending=False)

	title = f"""
	<h5>Number of Stories Published by Each Author By Year</h5>
	"""
	st.markdown(title, unsafe_allow_html=True)

	# Display the table
	heading_list = ['Author', 'Total', '1939', 
			'1940', '1941', '1942', '1943', '1944', '1945', '1946', '1947', '1948', '1949', 
			'1950', '1951', '1952', '1953', '1954', '1955', '1956', '1957', '1958', '1959', 
			'1960'] 
	st.set_page_config(layout="wide")
	show_data_table(author_year_pivot, heading_list, '1', '100px')

	show_csv_dl_button(author_year_pivot, 'storiesByYear.csv')

#### End of function show_author_by_year

#-------------------------------------------------------------------
def show_stacked_bar_chart():
##
## Display a bar chart with number of stories each year by the
## top 10 overall authors.
##

	default = 5

	with st.sidebar:
		num_authors = st.number_input('number of authors:', min_value=1, value=default, step=1)

	if "Total" in author_year_pivot.columns:
	    top_authors = author_year_pivot.sort_values("Total", ascending=False).head(num_authors)
	    top_authors = top_authors.drop(columns=["Total"])
	else:
	    top_authors = author_year_pivot.loc[author_year_pivot.sum(axis=1).nlargest(num_authors).index]

	top_authors = top_authors.drop(top_authors.columns[0], axis=1)
	year_author = top_authors.T # Transpose so years are rows, authors are columns

	title = f'Number of Stories Published Each Year by the Top {num_authors} Authors'

	show_plot_with_dl_button(year_author, 'bar', title)

#### End of function show_stacked_bar_chart

#-------------------------------------------------------------------
def author_count_by_year_df(an_author):
##
## Return a dataframe listing, for one author, the story counts for
## that author for each year, including zeros for years in which they
## published no stories.
##
	author_df    = df_all_stories[df_all_stories["Author"].str.contains(an_author, na=False)]
	story_counts = author_df.groupby('Year').agg(Num_Stories=('Year', 'count')).reset_index()

	year_list  = story_counts['Year'].tolist()
	count_list = story_counts['Num_Stories'].tolist()
	author_counts = pd.DataFrame({'Num_Stories': count_list}, index=year_list)

	# Reindex the two column dataframe using all years, filling with
	# zeros where this author had no stories in that year.
	all_keys = [1939, 
			1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 1948, 1949, 
			1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 
			1960] 
	author_counts = author_counts.reindex(all_keys, fill_value=0)

	return author_counts

#### End of function author_count_by_year_df

#-------------------------------------------------------------------
def plot_one_author(an_author):
##
## Display a line plot of stories published by a single author
## for each year.
##
	author_counts = author_count_by_year_df(an_author)
	num_stories   = author_counts['Num_Stories'].sum()
	show_plot_with_dl_button(author_counts, 'line', f'{an_author} Published {num_stories} Stories')

#### End of function plot_one_author

#-------------------------------------------------------------------
def show_one_author_plot():
##
## If no author has yet been selected, display an explaination
## for how this works, together with a sample plot output.
## Otherwise generate and display the line plot for the
## selected author.
##

	# Pull the authors column, turn it into a unique set of names,
	# convert that to a python list, and sort that into alpha order.
	# Use the sorted unique list of author names to present the user
	# with a drop down menu: which author should the plot be made for?
	author_list = sorted(set(df_all_stories['Author'].tolist()))
	with st.sidebar:
		author_name = st.selectbox(
		"pick an author:",
		(author_list),
		 index=None,
		 placeholder="Author...",
	)

	if author_name:
		plot_one_author(author_name)

	else:
		message = """
<style>
	.displayHead {{
	    font-family: Arial, Helvetica, sans-serif; 
	    font-size: 24px;
	    line-height: 1.5; 
	    color: #333; 
	}}
</style>
<h5>Stories per Year by One Author</h5><p class="displayHead">Pick an author from the menu on the left,
or click the menu and start typing an author's last name
to find the author in the list.
Your output will look something like the example below: a graph showing the number of 
stories published by Robert Heinlein each year, including those published under his 
pen names: Anson MacDonald and Caleb Saunders (each installment of a serial is counted 
as one story):
</p>
"""
		st.markdown(message, unsafe_allow_html=True)

		example = "Heinlein, Robert A."
		plot_one_author(example)

#### End of function show_one_author_plot

#-------------------------------------------------------------------
def plot_multiple_authors():
##
## 
##
	# Get a sorted list of all authors.
	author_list = sorted(set(df_all_stories['Author'].tolist()))

	# Show a drop down menu of all the authors.
	with st.sidebar:
		selected_authors = st.multiselect(
		    "Select one or more authors:",
		    author_list,
		    placeholder="pick authors"
		)
		clicked = st.button("Plot selected Authors")

	if selected_authors:

		# Generate the plot, but only if the button has been clicked.
		if clicked:
			count_lists = []
			authors     = []
			for this_author in selected_authors:
				author_counts = author_count_by_year_df(this_author)
				authors.append(this_author)
				count_lists.append(author_counts['Num_Stories'])

			year_list = list(range(1939, 1961))

			title = f"{len(authors)} authors: number of stories each year"
			show_multiline_plot_with_dl(year_list, count_lists, authors, title)

	else:
		message = """
<style>
	.displayHead {{
	    font-family: Arial, Helvetica, sans-serif; 
	    font-size: 24px;
	    line-height: 1.5; 
	    color: #333; 
	}}
</style>
<h5>Stories per Year by Multiple Authors</h5><p class="displayHead">Pick multiple authors from the menu on the left,
(or click the menu and start typing an author's last name
to find the author in the list).
Your output will look something like the example below: a graph showing the number of 
stories published by Robert Heinlein and Isaac Asimov each year, including those published under  
pen names: e.g. Anson MacDonald and Caleb Saunders for Heinlein. Note: each installment of a serial is counted 
as one story):
</p>
"""
		st.markdown(message, unsafe_allow_html=True)

		authors = []
		count_lists = []
		selected_authors = ["Heinlein, Robert A.", "Asimov, Isaac"]
		for this_author in selected_authors:
			author_counts = author_count_by_year_df(this_author)
			authors.append(this_author)
			count_lists.append(author_counts['Num_Stories'])

		year_list = list(range(1939, 1961))

		title = f"{len(authors)} authors: number of stories each year"
		show_multiline_plot_with_dl(year_list, count_lists, authors, title)


#### End of function show_select_authors

#-------------------------------------------------------------------
def show_top_n():
##
## 
##
	default = 20
	with st.sidebar:
		num_authors = st.number_input('number of authors:', min_value=1, value=default, step=1)

	top_authors = df_all_stories["Author"].value_counts().head(num_authors)
	show_plot_with_dl_button(top_authors, 'barh', f'Number of Stories by the Top {num_authors} Authors')

#### End of function show_top_20

#-------------------------------------------------------------------
def show_about():
##
##
##
	num_years   = df_all_stories['Year'].nunique()
	num_issues  = len(df_all_stories.drop_duplicates(subset=['Year', 'Month']))
	num_stories = len(df_all_stories)
	num_authors = df_all_stories['Author'].nunique()

	about = f"""
	<style>
		.about {{
		    font-family: Arial, Helvetica, sans-serif; 
		    font-size: 1.05rem;
		    line-height: 1.4; 
		    color: #333;
		    margin-top: 0;
		    margin-bottom: 8px;
		}}
		.title {{
		    font-family: Arial, Helvetica, sans-serif; 
		    font-size: 1.25rem;
		    font-weight: bold;
		}}
	</style>
	<div class="title">
	Science Fiction: The Golden Age
	</div>
	<div class="about">
	The golden age of pulp science fiction is generally agreed to have started in the late 1930s
	when John W. Campbell became editor of Astounding Science Fiction. There is
	less agreement as to the end of that era, but this web page uses the July 1939 and September 1960
	issues of Astounding as bookends for the golden age. 
	</div>
	<div class="about">
	The July 1939 issue included both the first published story by
	A. E. van Vogt, "Black Destroyer", and Isaac Asimov's first appearence in Astounding with "Trends". 
	Robert Heinlein's first story, "Life-Line", appeared in August, and September saw Theodore Sturgeon's
	first SF story, "Ether Breather".
	</div>
	<div class="about">
	The data here includes {num_stories:,} stories by {num_authors} authors in {num_issues} issues over {num_years} years.
	This web page provides various ways to explore and analyze that data.
	</div>
	<div class="about">
	Use the "Show..." menu on the left to choose a data visualization option. Some choices display tables, others 
	generate a plot or chart. Tables can be sorted by clicking on the heading of any column. The search field above
	a table can be used to filter results. For example, the screenshot below shows 'jenkins' entered into the search 
	field, resulting in the display of the single story that was published as written by Will F. Jenkins instead of 
	being published under his pen name Murray Leinster.
	<br>
	<img 
	src="https://github.com/ecurbsniktaw/ASF-Statistics/blob/b6d53fb758c9e23429795029b7a6b7c353f8b55c/data/tablesort.png?raw=true"
	border="1px">
	</div>
	<div class="title">
	About This Data
	</div>
	<div class="about">
	Thanks to Andrew May for creating a web page listing all the stories published in Astounding Science Fiction 
	during the golden age. 
	<a href="https://www.andrew-may.com/asf/list.htm" target="_blank">Here is his web page</a>, and some 
	<a href="https://www.andrew-may.com/bio.htm" target="_blank">information about Andrew</a>. 
	</div>
	<div class="about">
	The data on Andrew's page was converted into a spreadsheet using python code written jointly by ChatGPT and myself. 
	Once that spreadsheet was available, ChatGPT assisted in generating code to do some basic data analysis.
	</div>
	<div class="about">
	Creation of the current interactive web page was done without AI assistance, written in python, using the DataTables
	CSS/Javascript library for interactive HTML tables, and the Streamlit framework to build this interactive web page. 
	</div>
	"""

	st.markdown(about, unsafe_allow_html=True)

#### End of function show_about

##==================================================================================
##                               M  A  I  N                                       ##
##==================================================================================

# Read the two spreadsheets (all stories and author pivot) from this project's github repository
# and put that data into pandas dataframe objects: global variables.
all_stories_csv_github  = "https://raw.githubusercontent.com/ecurbsniktaw/ASF-Statistics/refs/heads/main/data/astounding_contents.csv"
author_pivot_csv_github = "https://raw.githubusercontent.com/ecurbsniktaw/ASF-Statistics/refs/heads/main/data/author_story_counts_by_year.csv"
df_all_stories    = read_df_from_csv(all_stories_csv_github)
author_year_pivot = read_df_from_csv(author_pivot_csv_github, True)

# Put a drop down menu into the page's sidebar, listing the options for
# displaying the story/author data as tables and as plots.
with st.sidebar:
	type_display = st.selectbox(
	"Pick a display...",
	("All stories", 
	 "Author totals", 
	 "Author by year",
	 "Bar chart: Top Authors",
	 "Plot: One Author",
	 "Plot: Multiple authors",
	 "Plot: Top N Authors",
	 "About This Site"),
	 index=None,
	 placeholder="Show...",
)
# End of sidebar

st.set_page_config(layout="wide")

if type_display:

	match type_display:

		case 'All stories':
			show_full_listing()

		case 'Author totals':
			show_author_totals()

		case 'Author by year':
			show_author_by_year()

		case 'Bar chart: Top Authors':
			show_stacked_bar_chart()

		case 'Plot: One Author':
			show_one_author_plot()

		case 'Plot: Multiple authors':
			plot_multiple_authors()

		case 'Plot: Top N Authors':
			show_top_n()

		case 'About This Site':
			show_about()

else:
	show_about() # Show about info when the page loads
