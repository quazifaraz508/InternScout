from django.shortcuts import render

# Create your models here.

import re
import csv
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from django.http import HttpResponse
from django.shortcuts import render
import os

def homePage(request):
    return render(request, 'homePage.html')

# Extract Internship Details Function
def extract_internship_details(text):
    """Extracts structured internship details from text using regex"""
    internships = []

    # Regex Patterns for extraction
    title_match = re.search(r'Actively hiring\s*\n([^\n]+)', text)
    company_match = re.search(r'Actively hiring\n[^\n]+\n([^\n]+)', text)
    location_match = re.search(r'\n([^\n]+)\nSTART DATE', text)
    start_date_match = re.search(r'START DATE\n([^\n]+)', text)
    duration_match = re.search(r'DURATION\n([^\n]+)', text)
    stipend_match = re.search(r'STIPEND\s*(?:₹\s*)?([\d,]+(?:-\d{1,3}(?:,\d{3})*)?)', text)
    stipend_match2 = re.search(r'₹\s*([\d,]+)\s*-\s*([\d,]+)', text)
    apply_by_match = re.search(r'APPLY BY\n([^\n]+)', text)
    skills_match = re.search(r'Skill\(s\) required\n([\s\S]+?)\n(?:Earn certifications|About the internship)', text)

    # Extract matches safely
    title = title_match.group(1).strip() if title_match else "N/A"
    company = company_match.group(1).strip() if company_match else "N/A"
    location = location_match.group(1).strip() if location_match else "N/A"
    start_date = start_date_match.group(1).strip() if start_date_match else "N/A"
    duration = duration_match.group(1).strip() if duration_match else "N/A"
    # stipend = stipend_match.group(1).strip() if stipend_match else "N/A"
 
    if stipend_match:
        stipend_min = stipend_match2.group(1).replace(',', '').strip()
        stipend_max = stipend_match2.group(2).replace(',', '').strip()
        stipend = f"{stipend_min} - {stipend_max}"
    elif stipend_match2:
        stipend = stipend_match.group(1).replace(',', '').strip()
    else:
        stipend = "N/A"

    apply_by = apply_by_match.group(1).strip() if apply_by_match else "N/A"
    skills = skills_match.group(1).strip().replace("\n", ", ") if skills_match else "N/A"

    return [title, company, location, start_date, duration, stipend, apply_by, skills]

# Save Data to CSV
def save_to_csv(internships, filename="internships.csv"):
    """Save extracted internship details to a CSV file"""
    headers = ["Internship URL", "Title", "Company", "Location", "Start Date", "Duration", "Stipend", "Apply By", "Skills Required"]
    
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Write header row
        writer.writerows(internships)  # Write data

# Scrape Internshala
def scrape_internshala(keyword, no_of_intership):
    """Scrapes internship details from Internshala"""
    keyword_encoded = urllib.parse.quote(keyword)
    driver = webdriver.Chrome()

    internships_list = []

    try:
        driver.get(f"https://internshala.com/internships/keywords-{keyword_encoded}/")

        try:
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "close_popup"))
            )
            close_button.click()
        except:
            pass  # No popup found

        internships = driver.find_elements(By.CLASS_NAME, "individual_internship")

        for i in range(min(no_of_intership, len(internships))): 
            internships[i].click()
            driver.switch_to.window(driver.window_handles[-1])

            new_url = driver.current_url

            try:
                internship_details = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "detail_view"))
                )

                internship_text = internship_details.text
                internship_data = extract_internship_details(internship_text)
                internships_list.append([new_url] + internship_data)

            except:
                print(f"Skipping internship {i+1} due to error!")

            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

    return internships_list


def internship_view(request):
    internships_data = []
    csv_file = None
    if request.method == "POST":
        keyword = request.POST.get('keyword')
        num_internships = int(request.POST.get('num_internships'))
        save_csv = request.POST.get('save_csv') == 'true'

        internships_data = scrape_internshala(keyword, num_internships)

        if save_csv:
            save_to_csv(internships_data, f"{keyword}_internships.csv")
            csv_file = f"{keyword}_internships.csv"
            # Store internships_data in session
            request.session['internships_data'] = internships_data  # Store in session

    return render(request, 'projects.html', {
        'internships': internships_data,
        'csv_file': csv_file
    })


# Django response to download CSV file
# def download_csv(request, filename):
#     filepath = os.path.join('media/csv/', filename)
#     with open(filepath, 'rb') as file:
#         response = HttpResponse(file.read(), content_type='text/csv')
#         response['Content-Disposition'] = f'attachment; filename={filename}'
#         return response

import io
import csv
from django.http import HttpResponse

def download_csv(request, filename):
    # Retrieve internships data from session
    internships_data = request.session.get('internships_data', [])

    if not internships_data:
        return HttpResponse("No internship data found.", status=404)

    # Create an in-memory buffer
    buffer = io.StringIO()
    
    # Define CSV headers
    headers = ["Internship URL", "Title", "Company", "Location", "Start Date", "Duration", "Stipend", "Apply By", "Skills Required"]
    
    # Create a CSV writer object
    writer = csv.writer(buffer)
    
    # Write header row
    writer.writerow(headers)
    
    # Write the internship data
    for internship in internships_data:
        writer.writerow(internship)
    
    # Seek back to the beginning of the buffer before sending it
    buffer.seek(0)
    
    # Create the response with the in-memory CSV file
    response = HttpResponse(buffer, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    return response
