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
edge_options.add_experimental_option("detach", True)

print("Uruchamiam Edge z profilem:", EDGE_PROFILE_PATH)
service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=edge_options)
driver.get(CRADLE_URL)
print("Otworzono stronę Cradle.")

wait = WebDriverWait(driver, 40)

try:
    print("Szukam zakładki 'My Team Tasks'...")
    my_team_tasks_tab = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(), 'My Team Tasks')] | //a[contains(text(), 'My Team Tasks')]")
        )
    )
    print("Klikam zakładkę 'My Team Tasks'...")
    my_team_tasks_tab.click()
    print("Zakładka kliknięta.")

    print("Szukam filtra 'QA final proofreading'...")
    qa_filter = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'QA final proofreading')]")
        )
    )
    print("Klikam filtr 'QA final proofreading'...")
    qa_filter.click()
    print("Filtr 'QA final proofreading' wybrany.")

    print("Szukam indexu kolumny 'Prod.Name'...")
    # Znajdź index kolumny "Prod.Name" (liczone od 1)
    headers = driver.find_elements(By.XPATH, "//table//th")
    prod_name_index = None
    for idx, th in enumerate(headers, 1):
        if "Prod.Name" in th.text:
            prod_name_index = idx
            break
    if prod_name_index is None:
        raise Exception("Nie znaleziono kolumny 'Prod.Name'!")

    print(f"Index kolumny 'Prod.Name': {prod_name_index}")

    print("Szukam pierwszego linku w kolumnie 'Prod.Name'...")
    asset_link = driver.find_element(
        By.XPATH,
        f"(//table//tr/td[{prod_name_index}]/a[@class='mj_link'])[1]"
    )

    print("Klikam pierwszy link w kolumnie 'Prod.Name'...")
    asset_link.click()
    print("Kliknięto pierwszy asset w 'Prod.Name'!")

    # --- tu kolejne kroki (np. kliknięcie Pending) ---

except Exception as e:
    print("Błąd podczas automatyzacji:", e)

input("Naciśnij Enter, aby zakończyć skrypt...")