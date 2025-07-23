from selenium import webdriver as wb
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import csv
import re
import pandas as pd

def monster_search(inputData):
    # Headless 옵션 추가 (서버에서 사용할 때 필수!)
    user_input = inputData

    options = Options()
    options.add_argument("--headless") # 창 없음
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = wb.Chrome(options=options)
    driver.maximize_window()
    # driver = wb.Chrome()

    driver.get("https://www.monsterzym.com/store/")
    time.sleep(1)
    search_keyword = driver.find_element(By.ID, "search_input")
    search_keyword.send_keys(user_input)
    search_keyword.send_keys(Keys.ENTER)
    time.sleep(3)


    # 스크롤하여 상품 모두 노출
    for _ in range(7):
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(0.2)
    # ★★★★★ 여기서 각 상품의 상세페이지 URL만 추출 ★★★★★
    search_items = driver.find_elements(By.CLASS_NAME, "ty-pict")
    print(f"총 {len(search_items)}개의 상품이 검색되었습니다.")
    product_links = []
    for item in search_items:
        try:
            parent_a = item.find_element(By.XPATH, "..")  # <a> 태그 상위
            link = parent_a.get_attribute("href")
            if link and link not in product_links:
                product_links.append(link)
        except Exception as e:
            print("링크 추출 실패:", e)
    product_list = []
    for i, link in enumerate(product_links):
        try:
            driver.get(link)
            time.sleep(0.2)
            title = driver.find_element(By.CLASS_NAME, "ty-product-block-title").text.strip()
            price = driver.find_element(By.CSS_SELECTOR, "span.ty-price-num.jq_sec_price_item").text.strip() + "원"
            try:
                img_tag = driver.find_element(By.CSS_SELECTOR, "a.cm-image-previewer.cm-previewer.ty-previewer")
                img_url = img_tag.get_attribute("href")
            except:
                img_url = "이미지 없음"
            page_url = driver.current_url
            i_list = driver.find_elements(By.CSS_SELECTOR, "a.cm-external-click > i")
            starCnt = 0
            halfStarCnt = 0
            for i_elem in i_list:
                cls = i_elem.get_attribute("class")
                if "star-half" in cls:
                    halfStarCnt += 1
                elif "icon-star" in cls:
                    starCnt += 1
            total_stars = starCnt / 2 + (0.5 * halfStarCnt / 2)
            sales_volume = "판매량 없음"
            vol_elements = driver.find_elements(By.CSS_SELECTOR, ".discussion_count")
            if vol_elements:
                sales_volume = vol_elements[0].text.strip()
            product_list.append([title, price, total_stars, sales_volume, img_url, page_url])
            print(f"{i+1}. {title} / {price} / 별점: {total_stars} / 판매량: {sales_volume}")
            print(f"   이미지: {img_url}")
            print(f"   페이지: {page_url}")
        except Exception as e:
            print(f"{i+1}번째 상품 크롤링 실패: {e}")
            continue
    driver.quit()
    with open("monster_product_list.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["상품명", "가격", "별점", "판매량", "이미지 URL", "상품 페이지 URL"])
        writer.writerows(product_list)
    print(":흰색_확인_표시: 크롤링 완료 및 CSV 저장 완료!")
    # ------------------ 점수 계산 및 정렬 ---------------------
    df = pd.read_csv("monster_product_list.csv")
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
    df_sorted.to_csv(f"monster_product_ranked.csv", index=False, encoding="utf-8-sig", float_format="%.5f")
    print(f":흰색_확인_표시: 점수 계산 완료 및 monster_product_ranked.csv 저장 완료!")