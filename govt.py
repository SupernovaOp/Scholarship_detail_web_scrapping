import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import gradio as gr
import time

# Base URL for scraping list of scholarships
base_url = "https://www.scholarshipforme.com/scholarships?state=&qualification=&category=&availability=&origin=&type=&page={}&is_item=true"

# List to store the scraped data
scholarship_list = []

# Function to scrape a single page
def scrape_page(page_number):
    url = base_url.format(page_number)
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all div elements with the class name "job-content"
    job_content_divs = soup.find_all("div", class_="job-content")

    # Extract the text of the anchor tag inside the h4 tag
    for div in job_content_divs:
        h4_tag = div.find("h4")
        if h4_tag and h4_tag.find("a"):
            anchor_tag = h4_tag.find("a")
            scholarship_list.append(anchor_tag.text)

# Function to scrape details of a single scholarship
def scrape_scholarship_details(endpoint):
    detail_base_url = "https://www.scholarshipforme.com/scholarships/"
    url = detail_base_url + endpoint
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (without opening a browser window)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    print(f"Scraping details from {url}...")
    driver.get(url)
    time.sleep(2)  # Wait for the page to load

    details = {
        "Scholarship Details": "",
        "Award": "",
        "Eligibility": "",
        "Documents Needed": "",
        "Provider": "",
        "How To Apply": "",
        "Published on": "",
        "Status": "",
        "Category": "",
        "Type": "",
        "State": "",
        "Gender": "",
        "Amount": "",
        "Application Deadline": "",
        "Official Link": "",
    }

    try:
        job_details_body = driver.find_element(By.CLASS_NAME, "job-details-body")
        current_section = None
        for elem in job_details_body.find_elements(By.XPATH, "./*"):
            if elem.tag_name == "h6":
                current_section = elem.text.strip()

            elif elem.tag_name == "p" or elem.tag_name == "ul":
                if current_section in details:
                    details[current_section] += elem.text.strip() + " "

        # Clean up the details
        for key in details:
            details[key] = details[key].strip()

        # Scrape additional details from the job overview list
        job_overview = driver.find_element(By.CLASS_NAME, "job-overview")
        for li in job_overview.find_elements(By.TAG_NAME, "li"):
            text = li.text
            if ":" in text:
                label, value = text.split(":", 1)
                label = label.strip()
                value = value.strip()
                if label in details:
                    details[label] = value
    except Exception as e:
        print(f"Error scraping {url}: {e}")

    driver.quit()
    return details

# Function to handle the scraping process and return results
def scrape_scholarships():
    page_number = 1
    while page_number < 4:
        print(f"Scraping page {page_number}...")
        initial_len = len(scholarship_list)
        scrape_page(page_number)

        # Check if new data was added, if not, break the loop
        if len(scholarship_list) == initial_len:
            break

        page_number += 1

    # Format the list by removing ',' and ';', replacing spaces with hyphens, and converting to lowercase
    formatted_list = [
        name.replace(",", "")
        .replace(";", "")
        .replace("(", "")
        .replace(")", "")
        .replace("'", " ")
        .replace(" ", "-")
        .lower()
        for name in scholarship_list
    ]

    print(f"Formatted list: {formatted_list}")

    # Scrape details for each formatted endpoint
    all_details = []
    for endpoint in formatted_list:
        details = scrape_scholarship_details(endpoint)
        if any(details.values()):  # Only append if there is any data
            details['Scholarship'] = endpoint.replace('-', ' ').title()
            all_details.append(details)

    return all_details

# Gradio Interface
def get_scholarship_details():
    result = scrape_scholarships()
    return result

# Create a Gradio interface
iface = gr.Interface(
    fn=get_scholarship_details,
    inputs=[],
    outputs=gr.JSON(),
    title="Scholarship Scraper",
    description="Scrapes scholarship details from ScholarshipForMe.com"
)

# Launch the Gradio interface
iface.launch()
