from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from bs4 import BeautifulSoup

# Initialize the Chrome driver
chrome_options = Options()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--headless")

def scrape_log(champ_name:str):
    champ_name = champ_name.lower()
    url = f'https://www.leagueofgraphs.com/champions/stats/{champ_name}'
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    html = None
    try:
        # Search for <table class="data_table sortable_table">
        table = driver.find_element(By.CLASS_NAME, "data_table")  
    except NoSuchElementException:
        print("Champion name incorrect")
    else:
        # Get the table's inner HTML
        html = table.get_attribute("innerHTML")  
    finally:
        driver.close()
    
    return html

def parse_log(html:str):
    # Parse the html
    soup = BeautifulSoup(html, "html.parser")

    # Look for <progressbar> tags with attribute data-color="wgblue"
    # and print their "data-value" attribute
    role_winrates = []
    for progressbar in soup.find_all("progressbar", {"data-color": "wgblue"}):
        wr = progressbar["data-value"]
        wr = float(f"{100*float(wr):.2f}")
        role_winrates.append(wr)

    top_roles = []
    # Look for all <a> tags in table
    for a in soup.find_all("a"):
        top_roles.append(a["filter-role"])

    role_winrates = dict(zip(top_roles, role_winrates))
    return role_winrates

def get_champ_roles(champ_name:str):
    html = scrape_log(champ_name)
    role_winrates = parse_log(html)
    return role_winrates