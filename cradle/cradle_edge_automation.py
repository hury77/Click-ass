from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time

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

    # Poczekaj, aż tabela się przeładuje (np. pojawi się pierwszy wiersz)
    print("Czekam na przeładowanie tabeli...")
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//table//tbody//tr[1]"))
    )
    time.sleep(1)  # (opcjonalnie, dla pewności)

    print("Szukam indexu kolumny 'Prod.Name' po odświeżeniu tabeli...")
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

    # --- czekamy na przeładowanie strony assetu ---
    time.sleep(3)
    # Jeśli asset otwiera się w nowej karcie – przełącz się:
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        print("Przełączono na nową kartę assetu.")
    else:
        print("Asset otworzył się w tej samej karcie.")

    # --- Kliknij Pending ---
    try:
        print("Szukam przycisku 'Pending'...")
        pending_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(translate(.,'pending','PENDING'),'PENDING')]")
            )
        )
        print("Klikam 'Pending'...")
        pending_btn.click()
        print("Kliknięto 'Pending'.")
    except TimeoutException:
        print("Nie znaleziono przycisku 'Pending'!")
        # Debug: wypisz wszystkie buttony
        btns = driver.find_elements(By.TAG_NAME, "button")
        for b in btns:
            print("BUTTON:", b.text)
        input("Sprawdź powyższe teksty buttonów i naciśnij Enter.")

    # --- Kliknij Take na popupie ---
    try:
        print("Szukam przycisku 'Take' na popupie...")
        take_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(translate(.,'take','TAKE'),'TAKE')]")
            )
        )
        print("Klikam 'Take'...")
        take_btn.click()
        print("Kliknięto 'Take'.")
    except TimeoutException:
        print("Nie znaleziono przycisku 'Take'!")
        btns = driver.find_elements(By.TAG_NAME, "button")
        for b in btns:
            print("BUTTON:", b.text)
        input("Sprawdź powyższe teksty buttonów i naciśnij Enter.")

except Exception as e:
    print("Błąd podczas automatyzacji:", e)

input("Naciśnij Enter, aby zakończyć skrypt...")