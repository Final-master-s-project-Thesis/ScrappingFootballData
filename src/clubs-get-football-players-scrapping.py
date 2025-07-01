from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-notifications")
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
options.add_argument(f"user-agent={user_agent}")
prefs = {
    "profile.default_content_setting_values.cookies": 2,
    "profile.block_third_party_cookies": True,
}
options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

clubs = []
players = []

try:
    # Load existing CSV data
    try:
        with open("data/clubs.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            clubs = [row for row in reader]

        with open("data/part-data-players.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            players = [row for row in reader]
    except FileNotFoundError:
        print("CSV not created yet")

    countLimit = 0
    for club in clubs:
        if any(str(row["clubId"]) == str(club['id']) for row in players):
            continue

        driver.get(club['url']) 

        time.sleep(1)

        if "503 Service Unavailable" in driver.page_source:
            print("Página bloqueada temporalmente. Esperando...")
            time.sleep(60)
            driver.refresh()

        if countLimit == 0:
            # Wait
            time.sleep(1)
            iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/iframe")))
            driver.switch_to.frame(iframe)
            time.sleep(1)
            accept_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="notice"]/div[3]/div[1]/div/button')))
            accept_button.click()
            driver.switch_to.default_content()

        table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="yw1"]/table/tbody')))
        rows = table.find_elements(By.XPATH, './/tr')
        for row in rows:
            try:
                if not row.find_elements(By.XPATH, './/td[2]/table/tbody/tr[1]/td[2]/a'):
                    continue
            except Exception as e:
                continue

            player_name = row.find_element(By.XPATH, './/td[2]/table/tbody/tr[1]/td[2]/a').text
            player_url = row.find_element(By.XPATH, './/td[2]/table/tbody/tr[1]/td[2]/a').get_attribute("href")
            date_and_age = row.find_element(By.XPATH, './/td[3]').text
            player_born_date = date_and_age.split(" ")[0]
            player_age = int(date_and_age.split("(")[1].strip(")"))
            club_id = club['id']
            
            players.append({
                "id": len(players) + 1,
                "clubId": club_id,
                "name": player_name,
                "age": player_age,
                "bornDate": player_born_date,
                "url": player_url,
            })
        
            if players:
                with open("data/part-data-players.csv", mode="w", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=players[0].keys())
                    writer.writeheader()
                    writer.writerows(players)

        #countLimit += 1
        #if countLimit >= 2:
        #    break

except Exception as e:
    print(f"An error occurred: {e}")
    print("Error in the current page URL:", driver.current_url)
    driver.quit()