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
## Generate and return the text of an HTML table.
## rows_list:    a list of lists with the values for the rows,
## heading_list: text for the table headings.

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
## Return a pandas dataframe containing the number of stories by
## each author for each year. Assumes that the table of all
## stories has already been read into a global dataframe
## named df_all_stories.

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
## Displays a table, using the datatables css/javascript package so that the 
## table is able to be sorted, searched, and filtered.
## panda_df:     a pandas dataframe, 
## heading_list: heading titles, 
## sortCol:      column number to be sorted,
## sortHow:      sort direction, 
## widthCol:     column number to be forced to a specific width,
## widthVal:     width of that column.

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
def show_plot_with_dl_button(dataframe, which_type, title, trace=False):

	if trace:
		st.dataframe(dataframe)

	fig, ax = plt.subplots()

	match which_type:

		case 'bar':
			dataframe.plot(kind=which_type, stacked=True, ax=ax, title=title)

		case 'line':
			ax = dataframe.plot(kind=which_type, ax=ax, marker='.', title=title, grid=True)
			ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
			ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
			# ax.spines['left'].set_position(('data', 1939))
			ax.spines['bottom'].set_position(('data', 0))

		case 'barh':
			ax = dataframe.plot.barh(legend=False)
			ax.invert_yaxis()
			plt.title('Number of Stories by The Top 20 Authors')
			plt.xlabel('Number of Stories')
			plt.ylabel('')

	plt.tight_layout()
	st.set_page_config(layout="centered")
	st.pyplot(fig)

	# Save the plot to a BytesIO object as PDF
	pdf_buffer = io.BytesIO()
	plt.savefig(pdf_buffer, format="pdf", bbox_inches="tight")
	pdf_buffer.seek(0)

	# Provide a download button for the PDF
	with st.sidebar:
	    st.download_button(
	        label="Download Plot as PDF",
	        data=pdf_buffer,
	        file_name="matplotlib_plot.pdf",
	        mime="application/pdf"
	    )

	# Close the Matplotlib figure to free up memory
	plt.close()

#### End of function show_plot_with_dl_button

#-------------------------------------------------------------------
def show_csv_dl_button(df, dl_file_name):

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
	st.set_page_config(layout="wide")
	heading_list = ['Seq', 'Year', 'Month', 'Title', 'Pub As', 'Author']
	show_data_table(df_all_stories, heading_list,'1', '25px')

	show_csv_dl_button(df_all_stories, 'allStories.csv')

#### End of function show_full_listing

#-------------------------------------------------------------------
def show_author_totals():
	author_counts = df_all_stories.groupby("Author").size().reset_index(name="StoryCount")
	author_counts.sort_values(by='StoryCount', ascending=False, inplace=True)

	heading_list = ['Author', 'Story Count']
	st.set_page_config(layout="centered")
	show_data_table(author_counts, heading_list, '0', '25%')

	show_csv_dl_button(author_counts, 'authorTotals.csv')


#### End of function show_author_totals

#-------------------------------------------------------------------
def show_author_by_year():
	author_year_pivot = author_pivot()

	# Move the totals to column 2, so you don't have to scroll to the right to see it.
	new_heads = ['Author', 'Total', 1939, 
			1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 1948, 1949, 
			1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 
			1960] 
	author_year_pivot = author_year_pivot[new_heads]
	author_year_pivot = author_year_pivot.sort_values(by='Total', ascending=False)

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
	if "Total" in author_year_pivot.columns:
	    top10_authors = author_year_pivot.sort_values("Total", ascending=False).head(10)
	    top10_authors = top10_authors.drop(columns=["Total"])
	else:
	    top10_authors = author_year_pivot.loc[author_year_pivot.sum(axis=1).nlargest(10).index]

	top10_authors = top10_authors.drop(top10_authors.columns[0], axis=1)
	year_author   = top10_authors.T # Transpose so years are rows, authors are columns

	show_plot_with_dl_button(year_author, 'bar', 'Top 10 Authors')

#### End of function show_stacked_bar_chart

#-------------------------------------------------------------------
def show_one_author_plot(trace=False):
	# Pull the authors column, turn it into a unique set of names,
	# convert that to a python list, and sort that into alpha order.
	author_list = sorted(set(df_all_stories['Author'].tolist()))

	# Use the sorted unique list of author names to present the user
	# with a drop down menu: which author should the plot be made for?
	with st.sidebar:
		author_name = st.selectbox(
		"pick an author:",
		(author_list),
		 index=None,
		 placeholder="Author...",
	)

	if author_name:

		# Pull the stories by the author that was chosen, and count them by year.
		author_df    = df_all_stories[df_all_stories["Author"].str.contains(author_name, na=False)]
		num_stories  = len(author_df)
		story_counts = author_df.groupby('Year').agg(Num_Stories=('Year', 'count')).reset_index()

		year_list  = story_counts['Year'].tolist()
		count_list = story_counts['Num_Stories'].tolist()
		new_counts = pd.DataFrame({'Num_Stories': count_list}, index=year_list)

		# Reindex the two column dataframe using all years, filling with
		# zeros where this author had no stories in that year.
		all_keys = [1939, 
				1940, 1941, 1942, 1943, 1944, 1945, 1946, 1947, 1948, 1949, 
				1950, 1951, 1952, 1953, 1954, 1955, 1956, 1957, 1958, 1959, 
				1960] 
		new_counts = new_counts.reindex(all_keys, fill_value=0)

		show_plot_with_dl_button(new_counts, 'line', f"{num_stories} stories by {author_name}")

	else:
		message = """
<center>
<h4>
Pick an author from the drop down menu on the left,<br>
or click on the menu and start typing an author's last name<br>
in order to find that author in the drop down list.
</h4>
</center>
		"""
		st.markdown(message, unsafe_allow_html=True)

#### End of function show_one_author_plot

#-------------------------------------------------------------------
def show_select_authors():
	st.write('will show plot select authors')

#### End of function show_select_authors

#-------------------------------------------------------------------
def show_top_20():

	top_authors = df_all_stories["Author"].value_counts().head(20)
	show_plot_with_dl_button(top_authors, 'barh', "Top 20 Most Frequent Authors (1939–1960)")

#### End of function show_top_20


##==================================================================================
##                               M  A  I  N                                       ##
##==================================================================================

df_all_stories    = read_df_from_csv("https://brucewatkins.org/sciencefiction/data/astounding_contents.csv")
author_year_pivot = read_df_from_csv("https://brucewatkins.org/sciencefiction/data/author_story_counts_by_year.csv", True)

num_years   = df_all_stories['Year'].nunique()
num_issues  = len(df_all_stories.drop_duplicates(subset=['Year', 'Month']))
num_stories = len(df_all_stories)
num_authors = df_all_stories['Author'].nunique()

heading = f"""
<center>
<h5>
Astounding Science Fiction<br>
{num_stories:,} stories by {num_authors} authors in {num_issues} issues over {num_years} years<br>
from July 1939 to September 1960
</h5>
</center>
"""
st.markdown(heading, unsafe_allow_html=True)

#------------------------------------------------
# SIDEBAR
#	Drop down menu with output options.
with st.sidebar:
	type_display = st.selectbox(
	"label",
	("Full listing", 
	 "Author totals", 
	 "Author by year",
	 "Plot: Stacked bar chart",
	 "Stories/yr, 1 Author",
	 "Plot: Select authors",
	 "Plot: Top 20 Authors"),
	 index=None,
	 label_visibility='hidden',
	 placeholder="Output...",
)
# End of sidebar
#------------------------------------------------

if type_display:

	match type_display:

		case 'Full listing':
			show_full_listing()

		case 'Author totals':
			show_author_totals()

		case 'Author by year':
			show_author_by_year()

		case 'Plot: Stacked bar chart':
			show_stacked_bar_chart()

		case 'Stories/yr, 1 Author':
			show_one_author_plot()

		case 'Plot: Select authors':
			show_select_authors()

		case 'Plot: Top 20 Authors':
			show_top_20()

else:
	show_full_listing() # Show full listing when page loads
