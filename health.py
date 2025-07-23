from selenium import webdriver as wb
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import csv
import re
import pandas as pd
import os
from selenium.webdriver.chrome.options import Options

def health_search(input_data):
    user_input = input_data

    options = Options()
    options.add_argument("--headless") # 창 없음
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = wb.Chrome(options=options)
    driver.maximize_window()

    driver.get("https://www.healthkoreaus.com/mall/index.php")
    time.sleep(1)
    # 검색
    search_keyword = driver.find_element(By.NAME, "ps_search")
    search_keyword.send_keys(user_input)
    search_keyword.send_keys(Keys.ENTER)
    time.sleep(1)  # 검색 결과 뜨는 시간만 최소로
    # 스크롤 (횟수, 딜레이 줄임)
    for _ in range(3):  # 필요 이상 스크롤은 X (보통 3~4번이면 충분)
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
        time.sleep(0.4)
    imgs = driver.find_elements(By.CLASS_NAME, "pull-left")
    print(f"총 {len(imgs)}개의 상품(이미지)이 검색되었습니다.")
    # 진짜 상품(링크 있는 것)만 리스트화
    product_links = []
    for img in imgs:
        try:
            parent_a = img.find_element(By.XPATH, "..")
            link = parent_a.get_attribute("href")
            if link and isinstance(link, str):
                product_links.append(link)
        except:
            continue
    print(f"총 {len(product_links)}개의 상품 링크가 수집되었습니다.")
    product_list = []
    for idx, link in enumerate(product_links):
        try:
            driver.get(link)
            time.sleep(0.2)  # 상품 상세 진입 대기 줄임
            # 상품명
            try:
                title = driver.find_element(By.CLASS_NAME, "mtop40").text.strip()
            except Exception as e:
                print(f"{idx+1}번째 상품명 추출 실패: {e}")
                title = "상품명 없음"
            # 가격
            try:
                price = driver.find_element(By.NAME, "option_money").get_attribute("value").strip()
            except Exception as e:
                print(f"{idx+1}번째 가격 추출 실패: {e}")
                price = "가격 없음"
            # 이미지 추출  (url)
            try:
                img_tag = driver.find_element(By.CSS_SELECTOR, "div.magnify img")
                img_url = img_tag.get_attribute("src")
                if img_url.startswith("/"):
                    img_url = "https://www.healthkoreaus.com" + img_url
            except Exception as e:
                print(f"{idx+1}번째 이미지 추출 실패: {e}")
                img_url = "이미지 없음"
            page_url = driver.current_url
            # 별점
            try:
                td = driver.find_element(By.XPATH, "//td[img[contains(@src,'icon_star')]]")
                full_stars = td.find_elements(By.XPATH, ".//img[contains(@src, 'icon_star.gif')]")
                half_stars = td.find_elements(By.XPATH, ".//img[contains(@src, 'icon_star_ban.gif')]")
                total_stars = len(full_stars) + 0.5 * len(half_stars)
            except Exception as e:
                print(f"{idx+1}번째 별점 추출 실패: {e}")
                total_stars = 0
            # 판매량
            try:
                sales_volume = driver.find_element(By.CLASS_NAME, "rating-number").text
                sales_volume = re.sub(r"[^\d]", "", sales_volume)
            except:
                sales_volume = "0"
            product_list.append([
                title, price, total_stars, sales_volume, img_url, page_url
            ])
            print(f"{idx+1}. {title} / {price} / 별점: {total_stars} / 판매량: {sales_volume}")
            driver.back()
            time.sleep(0.2)  # 뒤로가기 후 최소 대기
        except Exception as e:
            print(f"{idx+1}번째 상품 크롤링 실패: {e}")
            continue
    driver.quit()
    # ---------- CSV 저장 ----------
    csv_path = "healthkorea_product_list.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["상품명", "가격", "별점", "판매량", "이미지 URL", "상품 페이지 URL"])
        writer.writerows(product_list)
    print(":흰색_확인_표시: 크롤링 완료 및 CSV 저장 완료! (경로: {})".format(csv_path))
    # ---------- 점수 계산/랭킹 ----------
    df = pd.read_csv(csv_path)
    def clean_price(price_str):
        try:
            num = re.findall(r"\d+", str(price_str))
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
    df_sorted.to_csv(
        "healthkorea_product_ranked.csv",
        index=False,
        encoding="utf-8-sig",
        float_format="%.5f"
    )
    print(":흰색_확인_표시: 점수 계산 완료 및 healthkorea_product_ranked.csv 저장 완료!")