import os
import time
import shutil
import requests
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import zipfile

# Wczytaj .env
load_dotenv()
CRADLE_URL = os.getenv("CRADLE_URL")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")

EDGE_DRIVER_PATH = "/usr/local/bin/msedgedriver"
EDGE_PROFILE_PATH = "/Users/hubert.rycaj/Documents/Click-ass/CradleEdgeProfile"

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

    print("Czekam na przeładowanie tabeli...")
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//table//tbody//tr[1]"))
    )
    time.sleep(1)

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
        print("Nie znaleziono przycisku 'Pending'! Kontynuuję...")

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
        print("Nie znaleziono przycisku 'Take'! Kontynuuję...")

    # --- Szukanie pliku do pobrania (QC_final, potem QA Proofreading) ---
    file_url = None
    for section in ['QC_final', 'QA Proofreading']:
        try:
            print(f"Szukam linku do pliku w sekcji {section}...")
            file_link_elem = driver.find_element(
                By.XPATH, f"//td[contains(., '{section}')]/following-sibling::td//a[contains(@href, '.mp4') or contains(@href, '.mov') or contains(@href, '.zip')]"
            )
            file_url = file_link_elem.get_attribute('href')
            print(f"Znaleziony link do pliku: {file_url}")
            break
        except NoSuchElementException:
            print(f"Brak pliku w sekcji {section}. Szukam dalej...")

    if file_url:
        # Jeśli link jest względny, zbuduj pełny URL
        if file_url.startswith("/"):
            file_url = urljoin(CRADLE_URL, file_url)
            print("Absolutny URL pliku:", file_url)

        # Skopiuj cookies z Selenium do requests
        print("Pobieram cookies sesji...")
        session = requests.Session()
        for cookie in driver.get_cookies():
            session.cookies.set(cookie['name'], cookie['value'])

        # Pobieranie pliku
        local_filename = os.path.join(DOWNLOAD_DIR, os.path.basename(file_url))
        print(f"Pobieram plik do: {local_filename}")

        with session.get(file_url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("Plik pobrany!")

        # Jeśli plik to zip — rozpakuj
        if local_filename.lower().endswith('.zip'):
            print("Rozpakowuję archiwum zip...")
            with zipfile.ZipFile(local_filename, 'r') as zip_ref:
                zip_ref.extractall(DOWNLOAD_DIR)
            print("Archiwum rozpakowane!")
    else:
        print("Nie znaleziono pliku do pobrania w sekcji QC_final ani QA Proofreading.")

    # --- Szukanie ścieżki sieciowej na stronie assetu ---
    try:
        print("Szukam ścieżki sieciowej ('/Volumes/...') na stronie assetu...")
        # Znajdź pierwszy <p>, którego tekst zaczyna się od '/Volumes/'
        path_elem = driver.find_element(
            By.XPATH, "//p[starts-with(normalize-space(), '/Volumes/')]"
        )
        network_path = path_elem.text.strip()
        print("Znaleziono ścieżkę sieciową:", network_path)
        # Skopiuj plik z sieci do download_dir
        basename = os.path.basename(network_path)
        target_path = os.path.join(DOWNLOAD_DIR, basename)
        print(f"Kopiuję plik z sieci {network_path} do {target_path}...")
        shutil.copy(network_path, target_path)
        print("Plik skopiowany!")
    except Exception as e:
        print("Nie znaleziono ścieżki sieciowej lub kopiowanie nie powiodło się (to nie błąd krytyczny).")
        print(e)

except Exception as e:
    print("Błąd podczas automatyzacji:", e)

input("Naciśnij Enter, aby zakończyć skrypt...")