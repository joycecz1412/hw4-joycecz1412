"""Catalog-downloader script and helper functions"""

import bs4 
import pandas as pd
import requests
from time import sleep
import re

#getting program page
programs = requests.get('http://collegecatalog.uchicago.edu/thecollege/programsofstudy/')
programs_text = programs.text 

#compiling links for all the majors
major_links = bs4.BeautifulSoup(programs_text, 'html.parser')
major_links = major_links.find('ul', attrs={'class':'nav leveltwo', 
                                'id':'/thecollege/programsofstudy/'})

#finding tags for each major 
tag = major_links.find_all('a')
link_ends = []
for val in tag:
    link_ends.append(val['href'])
    
major_source = []
for end in link_ends:
    temp_req = requests.get('http://collegecatalog.uchicago.edu/'+end)
    major_source.append(temp_req.text)

#html code that contains a list of a list of courses for each major
majors_list: list[list] = []

for end, text in zip(link_ends, major_source):
    temp_bs = bs4.BeautifulSoup(text, 'html.parser')
    course_descriptions = temp_bs.find_all('div', class_ = "courseblock main")
    if not course_descriptions:
        continue
    majors_list.append(course_descriptions)
    

course_dict: dict = {'Course ID': [], 'Course Name': [], 
                'Course Description': [], 'Term(s) Offered': [], 'Staff': [], 
                'Equivalent Courses': [], 'Prerequisites': []}

department_dict: dict = {'Department': [], 'Courses Offered': []} 

#compiling things... 
for major in majors_list: 
    department = major[0].find('strong').get_text().split('.')[0]
    department_dict['Department'].append(department[0:4])
    department_dict['Courses Offered'].append(len(major))
    
    for course in major: 
        #Course ID and Course Name
        course_id_name = str(course.find('strong').get_text()).split('.')
        course_dict['Course ID'].append(course_id_name[0])
        course_dict['Course Name'].append(course_id_name[1])
        
        #Extracting Course description
        course_description = course.find('p', class_="courseblockdesc").get_text()
        course_dict['Course Description'].append(course_description)
        
        course_html = str(course)
        # Find all course details
        course_details_tags = re.findall(r'<p class="courseblockdetail">(.*?)</p>', course_html, re.DOTALL)
        if course_details_tags: 
        # Iterate over each course detail
            for detail in course_details_tags:
                # Search for instructor(s) information
                instructor_text = re.search(r'Instructor\(s\):\s*(.*?)(?=<br/>|Terms Offered:)', detail)
                instructor = instructor_text.group(1).strip() if instructor_text else 'NaN'
                if 'Staff' in instructor:
                    course_dict['Staff'].append('NaN')
                else:
                    course_dict['Staff'].append(instructor)
        
                terms_text = re.search(r'Terms Offered:\s*(.*?)(?=<br/>)', detail)
                terms_offered = terms_text.group(1).strip() if terms_text else 'NaN'
                course_dict['Term(s) Offered'].append(terms_offered)
                
                equivalent_text = re.search(r'Equivalent Course\(s\):\s*(.*?)(?=<br/>)', detail)
                equivalent_courses = equivalent_text.group(1).strip() if equivalent_text else 'NaN'
                course_dict['Equivalent Courses'].append(equivalent_courses)
                
                prerequisite_text = re.search(r'Prerequisite\(s\):\s*(.*?)(?=<br/>)', detail)
                if prerequisite_text:
                    prerequisites = prerequisite_text.group(1).strip()
                    course_dict['Prerequisites'].append(prerequisites)
                else:
                    course_dict['Prerequisites'].append('NaN')
        else: 
            course_dict['Staff'].append('NaN')
            course_dict['Term(s) Offered'].append('NaN')
            course_dict['Equivalent Courses'].append('NaN')
            course_dict['Prerequisites'].append('NaN')

department_df = pd.DataFrame(department_dict)
courses_df = pd.DataFrame(course_dict)
department_df.to_csv('department_data.csv', index=False)
courses_df.to_csv('courses_data.csv', index=False) 

#Question 1
print(len(courses_df)) # 4584

#Question 2
courses_df['Course ID'] = courses_df['Course ID'].apply(lambda x: x.replace('\xa0', ' '))
courses_df.loc[courses_df['Course ID'] == 'DATA 11800']
equivalent_classes_list = courses_df['Equivalent Courses'].str.split(', ').apply(set)
duplicates = set().union(*equivalent_classes_list)
matching_courses = []
for index, row in courses_df.iterrows():
    course_id = row['Course ID']
    for course in duplicates:
        if course_id == course:
            matching_courses.append(course)

print(len(matching_courses))
#2128 --> number of double counted courses

#Question 3
courses_new = courses_df
dpt = []

for course in courses_new['Course ID']:
    dpt.append(course[0:4])
courses_new['Department'] = dpt

courses_new = courses_new[~courses_new['Course ID'].isin(matching_courses)]
dpt_course_counts = courses_new.groupby('Department')['Course ID'].nunique()
department_counts_sorted = dpt_course_counts.sort_values(ascending=False)
department_counts_df = pd.DataFrame(department_counts_sorted).reset_index()
department_counts_df.columns = ['Department', 'Number of Classes']
department_counts_df
department_counts_df.to_csv('classes_per_dpt.csv', index=False)

#I was confused by what the hw was asking for, so here is a table with all the English courses offered
eng_courses = courses_new.loc[courses_new['Department'] == 'ENGL'][['Course ID','Course Name']]
eng_courses.to_csv('eng_courses.csv', index=False)

#Question 4
autumn = 0
winter = 0
spring = 0
for season in courses_df['Term(s) Offered']:
    if 'Autumn' in season:
        autumn += 1
    if 'Winter' in season:
        winter += 1
    if 'Spring' in season:
        spring += 1
print(autumn, winter, spring) #975 1072 1187 


