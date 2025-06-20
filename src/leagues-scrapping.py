from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import csv
import os

def load_csv(filename):
    filepath = os.path.join("..", "data", filename)
    if os.path.exists(filepath):
        with open(filepath, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return [row for row in reader]
    else:
        return []
    
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--incognito")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-notifications")
prefs = {
    "profile.default_content_setting_values.cookies": 2,
    "profile.block_third_party_cookies": True,
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
leagues = []
clubs = []

try:
    # Load data from JSON file
    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'leagues-links.json')
    data = {}

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load existing CSV data
    try:
        with open("data/leagues.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            leagues = [row for row in reader]
    
        with open("data/clubs.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            clubs = [row for row in reader]
    except FileNotFoundError:
        print("CSV not created yet")

    # Scrapping leagues data
    i = 0
    for league in data:
        if any(str(row["leagueId"]) == str(league['id']) for row in clubs):
            continue  # Skip if already exists

        if league['division'] == 2:
            continue # Skip second division leagues

        driver.get(league['url'])

        # Wait
        time.sleep(2)
        iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/iframe")))
        driver.switch_to.frame(iframe)
        time.sleep(1)
        accept_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="notice"]/div[3]/div[1]/div/button')))
        accept_button.click()
        driver.switch_to.default_content()

        # Exctract league data
        quantityClubs = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="tm-main"]/header/div[5]/div/ul[1]/li[1]/span'))
        )
        quantityPlayers = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="tm-main"]/header/div[5]/div/ul[1]/li[2]/span'))
        )
        medianAge = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="tm-main"]/header/div[5]/div/ul[2]/li[2]/span'))
        )

        leagues.append({
            "id": league['id'],
            "name": league['name'],
            "country": league['country'],
            "division": league['division'],
            "quantityClubs": int(quantityClubs.text.split()[0]),
            "quantityPlayers": int(quantityPlayers.text),
            "medianAge": float(medianAge.text.replace(',', '.')),
            "url": league['url']
        })

        table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="yw1"]/table/tbody')))
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            club_name = row.find_element(By.XPATH, './/td[2]/a').text
            club_url = row.find_element(By.XPATH, './/td[2]/a').get_attribute('href')
            club_id = len(clubs) + 1
            club_number_player = int(row.find_element(By.XPATH, './/td[3]/a').text)
            club_median_age = float(row.find_element(By.XPATH, './/td[4]').text.replace(',', '.'))

            clubs.append({ 
                "id": club_id,
                "name": club_name,
                "numberPlayer": club_number_player,
                "medianAge": club_median_age,
                "leagueId": league['id'],
                "url": club_url,
            })

            if clubs:
                with open("data/clubs.csv", mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=clubs[0].keys())
                    writer.writeheader()
                    writer.writerows(clubs)
        
        if leagues:
            with open("data/leagues.csv", mode="w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=leagues[0].keys())
                writer.writeheader()
                writer.writerows(leagues)
        
        i += 1
        if i == 10 or len(leagues) == 10:
            break

    driver.close()

except Exception as e:
    print(f"An error occurred: {e}")
    print("Error in the current page URL:", driver.current_url)
