from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import pandas as pd

def scrape_analyst_stats_paginated():
    url = "https://theanalyst.com/competition/premier-league/stats"

    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_opts)
    wait = WebDriverWait(driver, 10)

    all_rows = []
    headers = None

    try:
        driver.get(url)
        time.sleep(5)  # wait for page + JS

        while True:
            # Parse current table
            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table")

            if not table:
                print("No table found, breaking...")
                break

            # Extract headers once
            if headers is None:
                thead = table.find("thead")
                if thead:
                    headers = [th.get_text(strip=True) for th in thead.find_all("th")]
                else:
                    first_row = table.find("tr")
                    headers = [td.get_text(strip=True) for td in first_row.find_all(["th", "td"])]

            # Extract table rows
            tbody = table.find("tbody")
            for tr in tbody.find_all("tr"):
                tds = tr.find_all("td")
                row = [td.get_text(strip=True) for td in tds]
                all_rows.append(row)

            # Check pagination info
            pagination = soup.find("div", class_="TablePagination-module_pagination-container__yN7kR")
            if not pagination:
                print("No pagination div found, assuming only one page.")
                break

            span = pagination.find("span")
            page_info = span.get_text(strip=True) if span else ""
            print("Current page:", page_info)

            # Try to find the 'next' button
            buttons = pagination.find_all("button")
            if len(buttons) < 2:
                print("No next button found.")
                break

            next_button = buttons[1]  # second button is ">"
            # Stop if we're already on the last page
            if "of" in page_info:
                current_page, total_pages = [int(x) for x in page_info.replace(" ", "").split("of")]
                if current_page >= total_pages:
                    print("Reached last page.")
                    break

            # Click the next page button via Selenium
            next_btn_el = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'TablePagination')]/button[2]")))
            next_btn_el.click()
            time.sleep(3)  # wait for new data to load

        # Build DataFrame
        df = pd.DataFrame(all_rows, columns=headers)
        return df

    finally:
        driver.quit()


if __name__ == "__main__":
    df_all = scrape_analyst_stats_paginated()
    if df_all is not None:
        print(df_all.head())
        df_all.to_csv("analyst_premier_league_all_pages.csv", index=False)
        print("Saved all pages to CSV.")
