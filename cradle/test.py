from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service

EDGE_DRIVER_PATH = "/usr/local/bin/msedgedriver"
EDGE_PROFILE_PATH = "/Users/hubert.rycaj/Documents/Click-ass/CradleEdgeProfile"

edge_options = Options()
edge_options.add_argument(f"--user-data-dir={EDGE_PROFILE_PATH}")
edge_options.add_experimental_option("detach", True)

print("Używam profilu Edge:", EDGE_PROFILE_PATH)

service = Service(EDGE_DRIVER_PATH)
driver = webdriver.Edge(service=service, options=edge_options)
driver.get("https://cradle.egplusww.pl")
input("Naciśnij Enter, aby zakończyć skrypt...")