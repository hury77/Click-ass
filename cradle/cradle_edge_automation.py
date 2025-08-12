import os
import time
import shutil
import requests
from urllib.parse import urljoin, unquote, urlparse
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
import zipfile
from datetime import datetime

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg_full = f"[{ts}] {msg}"
    print(msg_full)
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(msg_full + "\n")

# Wczytaj .env
load_dotenv()
CRADLE_URL = os.getenv("CRADLE_URL")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR")

EDGE_DRIVER_PATH = "/usr/local/bin/msedgedriver"
EDGE_PROFILE_PATH = "/Users/hubert.rycaj/Documents/Click-ass/CradleEdgeProfile"

edge_options = Options()
edge_options.add_argument(f"--user-data-dir={EDGE_PROFILE_PATH}")
edge_options.add_experimental_option("detach", True)

log(f"Uruchamiam Edge z profilem: {EDGE_PROFILE_PATH}")
service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=edge_options)
driver.get(CRADLE_URL)
log("Otworzono stronę Cradle.")

wait = WebDriverWait(driver, 40)

try:
    log("Szukam zakładki 'My Team Tasks'...")
    my_team_tasks_tab = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//span[contains(text(), 'My Team Tasks')] | //a[contains(text(), 'My Team Tasks')]")
        )
    )
    log("Klikam zakładkę 'My Team Tasks'...")
    my_team_tasks_tab.click()
    log("Zakładka kliknięta.")

    log("Szukam filtra 'QA final proofreading'...")
    qa_filter = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'QA final proofreading')]")
        )
    )
    log("Klikam filtr 'QA final proofreading'...")
    qa_filter.click()
    log("Filtr 'QA final proofreading' wybrany.")

    log("Czekam na przeładowanie tabeli...")
    wait.until(
        EC.presence_of_element_located((By.XPATH, "//table//tbody//tr[1]"))
    )
    time.sleep(1)

    log("Szukam indexu kolumny 'Prod.Name' po odświeżeniu tabeli...")
    headers = driver.find_elements(By.XPATH, "//table//th")
    prod_name_index = None
    for idx, th in enumerate(headers, 1):
        if "Prod.Name" in th.text:
            prod_name_index = idx
            break
    if prod_name_index is None:
        raise Exception("Nie znaleziono kolumny 'Prod.Name'!")

    log(f"Index kolumny 'Prod.Name': {prod_name_index}")

    log("Szukam pierwszego linku w kolumnie 'Prod.Name'...")
    asset_link = driver.find_element(
        By.XPATH,
        f"(//table//tr/td[{prod_name_index}]/a[@class='mj_link'])[1]"
    )
    log("Klikam pierwszy link w kolumnie 'Prod.Name'...")
    asset_link.click()
    log("Kliknięto pierwszy asset w 'Prod.Name'!")

    # --- czekamy na przeładowanie strony assetu ---
    time.sleep(3)
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])
        log("Przełączono na nową kartę assetu.")
    else:
        log("Asset otworzył się w tej samej karcie.")

    # --- Kliknij Pending ---
    try:
        log("Szukam przycisku 'Pending'...")
        pending_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(translate(.,'pending','PENDING'),'PENDING')]")
            )
        )
        log("Klikam 'Pending'...")
        pending_btn.click()
        log("Kliknięto 'Pending'.")
    except TimeoutException:
        log("Nie znaleziono przycisku 'Pending'! Kontynuuję...")

    # --- Kliknij Take na popupie ---
    try:
        log("Szukam przycisku 'Take' na popupie...")
        take_btn = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(translate(.,'take','TAKE'),'TAKE')]")
            )
        )
        log("Klikam 'Take'...")
        take_btn.click()
        log("Kliknięto 'Take'.")
    except TimeoutException:
        log("Nie znaleziono przycisku 'Take'! Kontynuuję...")

    # --- Szukanie pliku do pobrania (QC_final, potem QA Proofreading) ---
    file_url = None
    for section in ['QC_final', 'QA Proofreading']:
        try:
            log(f"Szukam linku do pliku w sekcji {section}...")
            file_link_elem = driver.find_element(
                By.XPATH, f"//td[contains(., '{section}')]/following-sibling::td//a[contains(@href, '.mp4') or contains(@href, '.mov') or contains(@href, '.zip')]"
            )
            file_url = file_link_elem.get_attribute('href')
            log(f"Znaleziony link do pliku w sekcji {section}: {file_url}")
            break
        except NoSuchElementException:
            log(f"Brak pliku w sekcji {section}. Szukam dalej...")

    # --- Szukanie i pobieranie pliku emisyjnego z Broadcast file preparation ---
    broadcast_url = None
    try:
        log("Szukam pliku w sekcji 'Broadcast file preparation'...")
        file_link_elem = driver.find_element(
            By.XPATH, "//td[contains(., 'Broadcast file preparation')]/following-sibling::td//a[contains(@href, '.zip') or contains(@href, '.mp4') or contains(@href, '.mov')]"
        )
        broadcast_url = file_link_elem.get_attribute('href')
        log("Znaleziony link do pliku (Broadcast): " + str(broadcast_url))
    except NoSuchElementException:
        log("Brak pliku w sekcji 'Broadcast file preparation'.")

    # --- Pobieranie pliku z sekcji QC_final/QA Proofreading lub Broadcast file preparation ---
    for url, label in [(file_url, "QC_final/QA Proofreading"), (broadcast_url, "Broadcast file preparation")]:
        if url:
            if url.startswith("/"):
                url = urljoin(CRADLE_URL, url)
                log(f"Absolutny URL pliku ({label}): {url}")

            log("Pobieram cookies sesji...")
            session = requests.Session()
            for cookie in driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])

            local_filename = os.path.join(DOWNLOAD_DIR, os.path.basename(url))
            log(f"Pobieram plik ({label}) do: {local_filename}")

            try:
                with session.get(url, stream=True) as r:
                    r.raise_for_status()
                    with open(local_filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                log(f"Plik ({label}) pobrany!")
            except Exception as e:
                log(f"Błąd przy pobieraniu pliku ({label})! {e}")

            if local_filename.lower().endswith('.zip'):
                try:
                    log(f"Rozpakowuję archiwum zip ({label})...")
                    with zipfile.ZipFile(local_filename, 'r') as zip_ref:
                        zip_ref.extractall(DOWNLOAD_DIR)
                    log(f"Archiwum ({label}) rozpakowane!")
                except Exception as e:
                    log(f"Błąd przy rozpakowywaniu zip ({label}): {e}")
        else:
            log(f"Nie znaleziono pliku do pobrania w sekcji {label}.")

    # --- Szukanie ścieżki sieciowej na stronie assetu ---
    try:
        log("Szukam ścieżki sieciowej ('/Volumes/...') na stronie assetu...")
        path_elem = driver.find_element(
            By.XPATH, "//p[starts-with(normalize-space(), '/Volumes/')]"
        )
        network_path = path_elem.text.strip()
        log("Znaleziono ścieżkę sieciową: " + network_path)

        log(f"Czy plik istnieje? {os.path.isfile(network_path)}")
        if os.path.isfile(network_path):
            basename = os.path.basename(network_path)
            target_path = os.path.join(DOWNLOAD_DIR, basename)
            log(f"Kopiuję plik z sieci {network_path} do {target_path}...")
            try:
                shutil.copy(network_path, target_path)
                log("Plik skopiowany!")
                if basename.lower().endswith('.zip'):
                    log("Rozpakowuję archiwum zip...")
                    with zipfile.ZipFile(target_path, 'r') as zip_ref:
                        zip_ref.extractall(DOWNLOAD_DIR)
                    log("Archiwum rozpakowane!")
            except Exception as e:
                log(f"Błąd podczas kopiowania pliku sieciowego: {e}")
        else:
            possible_ext = [".mp4", ".mov", ".zip", ".mp4.zip"]
            found = False
            for ext in possible_ext:
                test_path = network_path + ext
                log(f"Sprawdzam czy istnieje: {test_path} -> {os.path.isfile(test_path)}")
                if os.path.isfile(test_path):
                    basename = os.path.basename(test_path)
                    target_path = os.path.join(DOWNLOAD_DIR, basename)
                    log(f"Kopiuję plik z sieci {test_path} do {target_path}...")
                    try:
                        shutil.copy(test_path, target_path)
                        log("Plik skopiowany!")
                        if ext.endswith(".zip"):
                            log("Rozpakowuję archiwum zip...")
                            with zipfile.ZipFile(target_path, 'r') as zip_ref:
                                zip_ref.extractall(DOWNLOAD_DIR)
                            log("Archiwum rozpakowane!")
                        found = True
                        break
                    except Exception as e:
                        log(f"Błąd podczas kopiowania pliku z rozszerzeniem {ext}: {e}")
            if not found:
                log("Nie znaleziono pliku pod podaną ścieżką z żadnym z typowych rozszerzeń!")
    except Exception as e:
        log("Nie znaleziono ścieżki sieciowej lub kopiowanie nie powiodło się (to nie błąd krytyczny).")
        log(str(e))

    # --- LucidLink: tylko kopiowanie pliku przez Pythona ---
    try:
        log("Szukam linku LucidLink na stronie assetu...")
        lucid_elem = driver.find_element(By.XPATH, "//a[starts-with(@href, 'lucid://')]")
        lucid_url = lucid_elem.get_attribute('href')
        log("Znaleziono link LucidLink: " + lucid_url)

        # Parsujemy ścieżkę lokalną
        parsed = urlparse(lucid_url)
        lucid_path = unquote(parsed.path)
        lucid_host = parsed.hostname
        local_lucid_path = f"/Volumes/{lucid_host}{lucid_path}"
        log("Lokalna ścieżka LucidLink: " + local_lucid_path)

        # Kopiowanie pliku do Downloads bez użycia LucidLink, open, subprocess itd.
        target = os.path.join(DOWNLOAD_DIR, os.path.basename(local_lucid_path))
        if os.path.isfile(local_lucid_path):
            try:
                shutil.copy(local_lucid_path, target)
                log(f"Plik LucidLink skopiowany do {target}!")
            except Exception as e:
                log(f"Błąd podczas kopiowania pliku LucidLink: {e}")
        else:
            log(f"Plik {local_lucid_path} nie jest dostępny lokalnie. Upewnij się, że plik jest zsynchronizowany przez LucidLink (zielona ikonka w Finderze) i spróbuj ponownie.")
    except Exception as e:
        log("Nie znaleziono linku LucidLink lub kopiowanie nie powiodło się (to nie błąd krytyczny).")
        log(str(e))

except Exception as e:
    log("Błąd podczas automatyzacji: " + str(e))

input("Naciśnij Enter, aby zakończyć skrypt...")