import time
import re
import pandas as pd
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


ROOT = "https://www.tecnomat.it/it/prodotti/"
OUT_CSV = "tecnomat_catalog_onepage_per_leaf.csv"

# ---------------- SELECTORS (from your HTML) ----------------
L1_CARD = "div.tailored-service"
L1_TITLE = "h3.h3-service"
L1_LINK = "a.service-btn"

SUBCAT_LINK = "a.bm_elem-product"  # used for both level2 and level3

# Algolia listing products
PRODUCT_ITEM = "li.ais-Hits-item"
PRODUCT_WRAPPER = "div.result-wrapper"
PRODUCT_NAME = "h2[itemprop='name']"
PRODUCT_URL_META = "meta[itemprop='url']"
PRODUCT_IMAGE = "img[itemprop='image']"
PRODUCT_PRICE_GROSS = "span[data-price='gross']"
PRODUCT_PRICE_NET = "span[data-price='net']"
PRODUCT_UNIT = "span.price-label"
PRODUCT_AVAIL = "span.result-availability-text"
PRODUCT_PRICE_META = "meta[itemprop='lowPrice']"
PRODUCT_CURRENCY_META = "meta[itemprop='priceCurrency']"

# Algolia pagination (we will NOT paginate now)
NEXT_PAGE = "a.ais-Pagination-link--next"
# -----------------------------------------------------------

SCROLL_ROUNDS = 3
SCROLL_PAUSE = 1.0


def start_browser(visible=True):
    options = Options()
    if visible:
        options.add_argument("--start-maximized")
        options.add_experimental_option("detach", True)
    else:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")

    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def abs_url(href: str) -> str:
    return urljoin("https://www.tecnomat.it", href or "")


def scroll_some(driver):
    for _ in range(SCROLL_ROUNDS):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE)


def try_accept_cookies(driver):
    candidates = [
        "button#onetrust-accept-btn-handler",
        "button.accept-cookies",
        "button.cookie-accept",
        "button[aria-label*='Accetta']",
        "button[title*='Accetta']",
    ]
    for css in candidates:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, css)
            btn.click()
            time.sleep(1)
            return
        except:
            pass


def page_has_products(driver) -> bool:
    return len(driver.find_elements(By.CSS_SELECTOR, PRODUCT_ITEM)) > 0


def get_l1_categories(driver):
    driver.get(ROOT)
    time.sleep(3)
    try_accept_cookies(driver)

    cards = driver.find_elements(By.CSS_SELECTOR, L1_CARD)
    out = []
    for c in cards:
        try:
            title = clean(c.find_element(By.CSS_SELECTOR, L1_TITLE).text)
        except:
            title = ""
        try:
            href = c.find_element(By.CSS_SELECTOR, L1_LINK).get_attribute("href")
        except:
            href = ""

        url = abs_url(href)
        if title and url.startswith("https://www.tecnomat.it/it/c/"):
            out.append((title, url))

    # de-dup by url preserving order
    seen = set()
    uniq = []
    for t, u in out:
        if u in seen:
            continue
        seen.add(u)
        uniq.append((t, u))
    return uniq


def get_subcategories(driver):
    """
    From a category page, extract all subcategory URLs + titles.
    Works for both level2 and level3 because HTML is the same.
    """
    time.sleep(2)
    scroll_some(driver)

    elems = driver.find_elements(By.CSS_SELECTOR, SUBCAT_LINK)
    out = []
    for a in elems:
        href = a.get_attribute("href") or ""
        url = abs_url(href)
        if not url.startswith("https://www.tecnomat.it/it/c/"):
            continue
        title = clean(a.text)
        if title:
            out.append((title, url))

    # de-dup
    seen = set()
    uniq = []
    for t, u in out:
        if u in seen:
            continue
        seen.add(u)
        uniq.append((t, u))
    return uniq


def extract_one_page_products(driver, level1, level2, level3, leaf_url):
    """
    Scrape ONLY ONE page (no pagination) from this leaf listing page.
    """
    rows = []
    driver.get(leaf_url)
    time.sleep(3)
    try_accept_cookies(driver)

    scroll_some(driver)

    items = driver.find_elements(By.CSS_SELECTOR, PRODUCT_ITEM)
    print(f"      Products on page 1: {len(items)}")

    for p in items:
        try:
            wrapper = p.find_element(By.CSS_SELECTOR, PRODUCT_WRAPPER)
            sku = wrapper.get_attribute("data-sku") or ""
        except:
            sku = ""

        try:
            name = clean(p.find_element(By.CSS_SELECTOR, PRODUCT_NAME).text)
        except:
            name = ""

        try:
            url = p.find_element(By.CSS_SELECTOR, PRODUCT_URL_META).get_attribute("content") or ""
        except:
            url = ""

        try:
            image = p.find_element(By.CSS_SELECTOR, PRODUCT_IMAGE).get_attribute("src") or ""
        except:
            image = ""

        try:
            price_gross = clean(p.find_element(By.CSS_SELECTOR, PRODUCT_PRICE_GROSS).text)
        except:
            price_gross = ""

        try:
            price_net = clean(p.find_element(By.CSS_SELECTOR, PRODUCT_PRICE_NET).text)
        except:
            price_net = ""

        # unit label can appear multiple times; take the nearest visible text
        unit = ""
        try:
            unit = clean(p.find_element(By.CSS_SELECTOR, PRODUCT_UNIT).text)
        except:
            unit = ""

        try:
            availability = clean(p.find_element(By.CSS_SELECTOR, PRODUCT_AVAIL).text)
        except:
            availability = ""

        try:
            price_numeric = p.find_element(By.CSS_SELECTOR, PRODUCT_PRICE_META).get_attribute("content") or ""
        except:
            price_numeric = ""

        try:
            currency = p.find_element(By.CSS_SELECTOR, PRODUCT_CURRENCY_META).get_attribute("content") or ""
        except:
            currency = ""

        rows.append({
            "level1": level1,
            "level2": level2,
            "level3": level3,
            "sku": sku,
            "product_name": name,
            "product_url": url,
            "image_url": image,
            "price_gross": price_gross,
            "price_net": price_net,
            "price_numeric": price_numeric,
            "currency": currency,
            "unit": unit,
            "availability": availability,
            "leaf_url": leaf_url
        })

    return rows


def append_to_csv(rows, path):
    if not rows:
        return
    df = pd.DataFrame(rows)
    try:
        with open(path, "r", encoding="utf-8"):
            header = False
    except:
        header = True
    df.to_csv(path, mode="a", index=False, header=header, encoding="utf-8")


def main():
    driver = start_browser(visible=True)

    visited_category_urls = set()
    visited_leaf_urls = set()

    l1_list = get_l1_categories(driver)
    print(f"Found L1 categories: {len(l1_list)}")

    for l1_title, l1_url in l1_list:
        print(f"\n[L1] {l1_title} -> {l1_url}")
        if l1_url in visited_category_urls:
            continue
        visited_category_urls.add(l1_url)

        driver.get(l1_url)
        time.sleep(3)
        try_accept_cookies(driver)

        l2_list = get_subcategories(driver)
        print(f"  L2 count: {len(l2_list)}")

        # If no L2 and it is already a leaf listing:
        if not l2_list and page_has_products(driver):
            if l1_url not in visited_leaf_urls:
                print("  (L1 is a leaf listing) scraping page 1…")
                rows = extract_one_page_products(driver, l1_title, "", "", l1_url)
                append_to_csv(rows, OUT_CSV)
                visited_leaf_urls.add(l1_url)
            continue

        for l2_title, l2_url in l2_list:
            print(f"  [L2] {l2_title} -> {l2_url}")
            if l2_url in visited_category_urls:
                continue
            visited_category_urls.add(l2_url)

            driver.get(l2_url)
            time.sleep(3)
            try_accept_cookies(driver)

            # If L2 is already a leaf listing:
            if page_has_products(driver):
                if l2_url not in visited_leaf_urls:
                    print("    (L2 is a leaf listing) scraping page 1…")
                    rows = extract_one_page_products(driver, l1_title, l2_title, "", l2_url)
                    append_to_csv(rows, OUT_CSV)
                    visited_leaf_urls.add(l2_url)
                continue

            # Otherwise, find L3
            l3_list = get_subcategories(driver)
            print(f"    L3 count: {len(l3_list)}")

            # If no L3 and not listing, skip
            if not l3_list:
                print("    (No L3 and no products detected) skip")
                continue

            # IMPORTANT: We store URLs/titles, then navigate. No stale elements.
            for l3_title, l3_url in l3_list:
                print(f"    [L3] {l3_title} -> {l3_url}")

                # Don’t treat L3 as category hub forever; check leaf listing
                if l3_url in visited_leaf_urls:
                    continue

                driver.get(l3_url)
                time.sleep(3)
                try_accept_cookies(driver)

                if page_has_products(driver):
                    print("      (Leaf listing) scraping page 1…")
                    rows = extract_one_page_products(driver, l1_title, l2_title, l3_title, l3_url)
                    append_to_csv(rows, OUT_CSV)
                    visited_leaf_urls.add(l3_url)
                else:
                    # Some categories might be 4 levels deep. You can add L4 later.
                    print("      (No products detected on this L3 page)")

    print(f"\n✅ DONE. CSV saved to: {OUT_CSV}")


if __name__ == "__main__":
    main()