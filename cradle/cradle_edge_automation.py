from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

EDGE_DRIVER_PATH = "/usr/local/bin/msedgedriver"
EDGE_PROFILE_PATH = "/Users/hubert.rycaj/Documents/Click-ass/CradleEdgeProfile"
CRADLE_URL = "https://cradle.egplusww.pl"

edge_options = Options()
edge_options.add_argument(f"--user-data-dir={EDGE_PROFILE_PATH}")
edge_options.add_experimental_option("detach", True)  # Edge zostaje otwarty

print("Używam profilu Edge:", EDGE_PROFILE_PATH)

service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=edge_options)
driver.get(CRADLE_URL)
print("Otworzono stronę Cradle.")

wait = WebDriverWait(driver, 40)

try:
    print("Szukam zakładki 'My Team Tasks'...")
    my_team_tasks_tab = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'My Team Tasks')] | //a[contains(text(), 'My Team Tasks')]"))
    )
    print("Klikam w zakładkę 'My Team Tasks'...")
    my_team_tasks_tab.click()

    print("Szukam filtra 'QA final proofreading'...")
    qa_filter = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'QA final proofreading')]"))
    )
    print("Klikam filtr 'QA final proofreading'...")
    qa_filter.click()

    print("Kroki automatyzacji wykonane.")

except Exception as e:
    print("Błąd podczas wykonywania któregoś kroku:", e)

input("Naciśnij Enter, aby zakończyć skrypt...")
# NIE wywołuj driver.quit(), Edge zostaje otwarty