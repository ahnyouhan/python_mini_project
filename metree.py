from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time
import csv
import re
import pandas as pd

def metree_search(inputData):
    user_input = inputData
    # --- headless 옵션 추가 부분 ---
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('window-size=1920x1080')
    chrome_options.add_argument("lang=ko_KR")  # 한글 깨짐 방지
    # ---------------------------------
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.metree.co.kr/")
    time.sleep(1)
    # 팝업 처리 (이하 동일)
    popup_handled = False
    start_time = time.time()
    while time.time() - start_time < 5:
        try:
            popup = driver.find_element(By.CLASS_NAME, "mypage_pop_btn")
            buttons = popup.find_elements(By.TAG_NAME, "li")
            for btn in buttons:
                if "하루" in btn.text:
                    btn.click()
                    popup_handled = True
                    break
            if popup_handled:
                break
        except NoSuchElementException:
            pass
        time.sleep(0.5)
    # 검색
    search_keyword = driver.find_element(By.NAME, "search_str")
    search_keyword.click()
    search_keyword.send_keys(user_input)
    time.sleep(1)
    search_button = driver.find_element(By.CLASS_NAME, "ab")
    search_button.click()
    time.sleep(3)
    product_list = []
    page = 1
    while True:
        print(f"현재 페이지: {page}")
        time.sleep(2)
        products = driver.find_elements(By.CSS_SELECTOR, ".prd_basic.col4 li")
        print(f"상품 수: {len(products)}")
        for product in products:
            try:
                title = product.find_element(By.CLASS_NAME, "name").text.strip()
                price = product.find_element(By.CSS_SELECTOR, ".sell.sell").text.strip()
                sales_volume = product.find_element(By.CLASS_NAME, "numb").text.strip("()")
                star_div = product.find_element(By.CLASS_NAME, "star")
                total_stars = float(star_div.text.strip())
                img_url = product.find_element(By.TAG_NAME, "img").get_attribute("src")
                page_url = product.find_element(By.TAG_NAME, "a").get_attribute("href")
                product_list.append([
                    title, price, total_stars, sales_volume, img_url, page_url
                ])
                print(f"{title} / {price} / {total_stars} / {sales_volume}")
            except Exception as e:
                print(f"상품 처리 중 오류: {e}")
                continue
        # 다음 페이지
        try:
            page += 1
            next_page_link = driver.find_element(By.LINK_TEXT, str(page))
            driver.execute_script("arguments[0].click();", next_page_link)  # ← 이 부분만 바꿔주면 끝!
            time.sleep(2)
        except NoSuchElementException:
            print("마지막 페이지입니다. 크롤링 종료.")
            break
    driver.quit()
    print("크롤링 완료, 점수 계산 시작!")
    # 점수 계산
    df = pd.DataFrame(product_list, columns=[
        "상품명", "가격", "별점", "판매량", "이미지 URL", "상품 페이지 URL"
    ])
    def clean_price(price_str):
        try:
            num = re.findall(r"\d+", price_str)
            return int("".join(num)) if num else None
        except:
            return None
    df["가격(숫자)"] = df["가격"].apply(clean_price)
    def extract_sales(s):
        try:
            num = re.findall(r"\d+", str(s))
            return int(num[0]) if num else 0
        except:
            return 0
    df["판매량(숫자)"] = df["판매량"].apply(extract_sales)
    df = df.dropna(subset=["가격(숫자)", "별점", "판매량(숫자)"])
    min_price = df["가격(숫자)"].min()
    max_price = df["가격(숫자)"].max()
    min_sales = df["판매량(숫자)"].min()
    max_sales = df["판매량(숫자)"].max()
    print("최저가:", min_price, "최고가:", max_price)
    print("최소 판매량:", min_sales, "최대 판매량:", max_sales)
    df["가격 점수"] = 1 - (df["가격(숫자)"] - min_price) / (max_price - min_price + 1e-9)
    df["평점 점수"] = df["별점"] / 5
    df["판매량 점수"] = (df["판매량(숫자)"] - min_sales) / (max_sales - min_sales + 1e-9)
    df["최종 점수"] = (
        df["가격 점수"] * 0.2 +
        df["평점 점수"] * 0.1 +
        df["판매량 점수"] * 0.7
    )
    df_sorted = df.sort_values(by="최종 점수", ascending=False)
    df_sorted.to_csv("metree_product_ranked.csv", index=False, encoding="utf-8-sig", float_format="%.5f")
    print("점수 계산 완료 및 metree_product_ranked.csv 저장 완료")