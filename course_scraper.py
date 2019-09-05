from selenium import webdriver
import selenium.webdriver.chrome.service as service
from urllib.request import urlopen
import time
from bs4 import BeautifulSoup
import ssl
import pandas as pd
import csv

class Course_Scraper:
	def __init__(self, term, user_distribs):
		self.term = term
		self.user_distribs = user_distribs
		self.distribs_dict = {}
		self.course_weights_dict = {}
		self.TERM = []
		self.COURSE = []
		self.MEDIAN = []

	#makes all course names uniform
	#TODO: More to be done here
	def string_uniformer(self, course_str):
		print(course_str)
		#finds the indeed of the first two -'s and the first .
		hyphen_1_index = self.findnth(str(course_str), "-", 0)
		hyphen_2_index = self.findnth(str(course_str), "-", 1)
		point_1_index = self.findnth(str(course_str), ".", 0)

		if point_1_index == -1:
			num_cutoff = hyphen_2_index + 1
			center_num = int(course_str[hyphen_1_index + 1 : num_cutoff - 1])



		return (course_str)


	#we want to return AAAS-54.32-01
	#as AAAS-054.32-01
	# AAAS-9.2-12 as AAAS-009.2-12
	#find nth specific character
	
	def findnth(self, string, substring, n):
	    parts = string.split(substring, n + 1)
	    if len(parts) <= n + 1:
	        return -1
	    return len(string) - len(parts[-1]) - len(substring)

	#scrapes all required course medians of last n years from start date, 
	#returns array of arrays
	def median_scraper(self, time_period):
		print ("\nHere We Go\n ")
		#takes the 18 of 18F and goes back n years
		year = int(self.term[:2])
		curr_yr = year - time_period
		term_list = ["W", "S", "X", "F"]
		context = ssl._create_unverified_context()
		while curr_yr <= year:
			for curr_term in term_list:
				#make it go all the way to the last term before the current one
				if curr_yr < year or term_list.index(curr_term) < term_list.index(self.term[2]):
					#link to the appropriate medians page
					link = "https://www.dartmouth.edu/~reg/transcript/medians/" + str(curr_yr) + str(curr_term) + ".html"
					page = urlopen(link, context = context)
					soup = BeautifulSoup(page, features = "html.parser")
					medians_tab = soup.find("table")

					#put the info in a list we can use
					for row in medians_tab.find_all("tr"):
						cells = row.findAll('td')
						#if statement ensures titles of columns not included
						if len(cells) == 4 and "-" in (cells[1].find(string=True)):

							self.TERM.append(cells[0].find(string=True))
							self.COURSE.append(self.string_uniformer((cells[1].find(string=True))))
							#COURSE.append(cells[1].find(string=True))
							self.MEDIAN.append(cells[3].find(string=True))

			curr_yr += 1

		data = [self.TERM, self.COURSE, self.MEDIAN]
		self.place_into_dataframe(data)
		return [self.TERM, self.COURSE, self.MEDIAN]


	#places required term's courses in a datafram
	def place_into_dataframe(self, datalist):

		print ("Running dataframe placement: \n\n")
		print (datalist[1])

		df = pd.DataFrame(columns = ['TERM'])
		df['TERM'] = datalist[0]
		df['COURSE']= datalist[1]
		df['MEDIAN'] = datalist[2]


		df.to_csv('/Users/osmankhan/desktop/req_term_data.csv')


	#allows you to use already scraped medians
	def access_scraped_medians(self):
		return	

	def open_course_db_page(self):

		#webdriver automates chrome to access the course page
		options = webdriver.ChromeOptions()
		options.add_argument('--ignore-certificate-errors')
		options.add_argument("--test-type")
		options.binary_location = "/usr/bin/chromium"
		driver = webdriver.Chrome('//Users/osmankhan/Desktop/dartmouth_year_2/Scraper/chromedriver')


		driver.get('http://oracle-www.dartmouth.edu/dart/groucho/timetable.main')

		# click first button on first page

		python_button = driver.find_elements_by_xpath("//input[@name='searchtype' and @value='Subject Area(s)']")[0]
		python_button.click()

		# click first button on second page

		term_button = driver.find_elements_by_xpath("//input[@name='termradio' and @value='allterms']")[0]
		term_button.click()

		# click second button on second page

		subject_button = driver.find_elements_by_xpath("//input[@name='subjectradio' and @value='allsubjects']")[0]
		subject_button.click()

		# click third button on second page

		submit_button = driver.find_elements_by_xpath("//input[@type='submit' and @value='Search for Courses']")[0]
		submit_button.click()

		return(driver)

	#generates a list of all courses + their cultural and other distribs
	def make_course_database(self):

		#opens course page and gives us driver
		driver = self.open_course_db_page()

		soup = BeautifulSoup(driver.page_source, features="html.parser")
		courses_tab = soup.find('table', { "summary" : "Main page"})

		COURSENAME = []
		CULT_DIST = []
		DISTRIB = []


		for row in courses_tab.find_all("tr"):
			cells = row.findAll('td')
			if len(cells) == 19:

				full_name = (str(cells[2].find(string=True)) + "-" + str(cells[3].find(string=True))).strip(" ")
				#standardizes all course names, removes .042 for example
				#from the end of the course name
				#if str(cells[3]).find(".") != -1:
				#	truncate_point = full_name.index(".")
				#	COURSENAME.append(full_name[:truncate_point])

				#else:
				COURSENAME.append(full_name)

				culture_distribs = ["CI", "WC", "NW"]
				if not any (x in str(cells[13]) for x in culture_distribs):
					CULT_DIST.append("	")
				else:
					CULT_DIST.append(cells[13].find(string=True))

				distribs = ["TLA", "SCI", "SLA", "ART", "TMV", "INT", "LIT", "SOC", "TAS"]
				distrib_cell = cells[14].find(string=True).translate("<td>/")

				if not any (x in str(cells[14]) for x in distribs):
					DISTRIB.append("	")
				else:
					DISTRIB.append(distrib_cell)
		
		i = 0
		course_db = {}
		while i < len(COURSENAME):

			#if not(COURSENAME[i] == "WRIT-005" or COURSENAME == "WRIT-003"):
			course_db[self.string_uniformer(COURSENAME[i])] = [CULT_DIST[i], DISTRIB[i]]

			i += 1

		return course_db


	#
	def get_best(self):

		#req_medians is the list of all the medians from the past 4 years
		req_medians = self.median_scraper(4)
		i = 0
		weight_dict = {}


		while i < len(req_medians[0]):

			#creates a dictionary of all courses in the needed term and their median-scores
			#print(req_medians[1][i])

			if self.findnth(str(req_medians[1][i]), "-", 3) != -1:

				truncate_point = self.findnth(str(req_medians[1[i]]), "-", 2)
				req_medians[1][i] = str(req_medians[1][i][:truncate_point])


			if (req_medians[0][i])[2] == self.term[2]:

				if req_medians[1][i] not in weight_dict:

					if req_medians[2][i] == "A":
						weight_dict[req_medians[1][i]] = 7

					elif req_medians[2][i] == "A/A-":
						weight_dict[req_medians[1][i]] = 5.5

					elif req_medians[2][i] == "A-":
						weight_dict[req_medians[1][i]] = 4

					elif req_medians[2][i] == "B+":
						weight_dict[req_medians[1][i]] = 2

				else:

					if req_medians[2][i] == "A":
						weight_dict[req_medians[1][i]] += 7

					elif req_medians[2][i] == "A/A-":
						weight_dict[req_medians[1][i]] = 5.5

					elif req_medians[2][i] == "A-":
						weight_dict[req_medians[1][i]] += 4

					elif req_medians[2][i] == "B+":
						weight_dict[req_medians[1][i]] += 2					


			i += 1

		db1 = self.make_course_database()

		print(db1)

		for course in weight_dict:
			if self.findnth(str(course), "-", 1) != -1:
				truncate_point = self.findnth(course, "-", 1)
				course = str(course[:truncate_point]).strip()


			for dist in self.user_distribs:
				if dist in db1[course]:
					#print ("distrib weight added")
					weight_dict[course] += 7

		

		return weight_dict
		#weight_dict holds all courses and their weights according to their medians

"""
		#if there are no decimals, then the cutoff should be past the second index
		if point_1_index == -1:
			num_cutoff = hyphen_2_index + 1
			center_num = int(course_str[hyphen_1_index + 1 : num_cutoff - 1])

		if hyphen_2_index == -1:

			center_num = float(course_str[hyphen_1_index + 1:])

		if point_1_index != -1:
			num_cutoff = point_1_index + 2

			center_num = float(course_str[hyphen_1_index + 1: num_cutoff])



		#appends right number of zeros to middle number

		if center_num - int(center_num) == 0.0:
			center_num = int(center_num)
			center_str = str(center_num)
			print ("1 activated")

		if 9 < abs(center_num) <= 99 :
			print(course_str)
			center_str = "0" + str(center_num)
			print ("2 activated")

		elif abs(center_num) <= 9:
			center_str = "0" + "0" + str(center_num)
			print ("3 activated")

		elif 99 < abs(center_num):
			print ("Three digit ")
			center_str = str(center_num)
		#if no decimal
		if point_1_index == -1:

			if hyphen_2_index == -1:
				print ("4 activated")
				print(course_str)
				course_str = course_str[:hyphen_1_index] + "-" + center_str
				print(course_str)

			else:
				print ("5 activated")
				course_str = course_str[:hyphen_1_index] + "-" + center_str + course_str[hyphen_2_index :]


		else:
			print ("6 activated")
			print(course_str)
			course_str = course_str[:hyphen_1_index] + "-" + center_str + course_str[point_1_index + 2:]



		if hyphen_2_index != -1:
			print ("7 activated")
			course_str = course_str[:-3]
"""


