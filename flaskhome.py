from flask import Flask, render_template
from flask import request, redirect
import csv
import metree
import monster
import health
import os
import allProduct

app = Flask(__name__)
searchInput = ""

def loadProducts(csvName):
    productList = []
    if not os.path.exists(csvName):
        return productList
    
    with open(csvName, newline='', encoding='utf-8-sig') as file:
        readFile = csv.DictReader(file)
        for row in  readFile:
            productList.append({    
                'name': row['상품명'],
                'price': row['가격'],
                'imageLink': row['이미지 URL'],
                'productLink': row['상품 페이지 URL']
            })
    return productList

@app.route("/")
def index():
    site = request.args.get('site')
    global searchInput

    if site == 'metree':
        csvName = 'metree_product_ranked.csv' 
    elif site == 'monster':
        csvName = 'monster_product_ranked.csv'
    elif site == 'health':
        csvName = 'healthkorea_product_ranked.csv'
    elif site == 'all':
        csvName = "all_product_ranked.csv"
    else:
        # site 없거나 다른 값이면 빈 리스트 넘김
        productList = []
        return render_template("home.html", productList=productList)
    
    productList = loadProducts(csvName)
    return render_template("home.html", productList=productList)

@app.route('/search', methods=['GET'])
def search():
    global searchInput
    searchInput = request.args.get('searchInput', '')  # 쿼리 스트링에서 가져옴
    site = request.args.get('site', 'all')

    if site == 'metree':
        metree.metree_search(searchInput)  # 크롤링 실행
        csvName = 'metree_product_ranked.csv'
    elif site == 'monster':
        monster.monster_search(searchInput)
        csvName = 'monster_product_ranked.csv'
    elif site == 'health':
        health.health_search(searchInput)
        csvName = 'healthkorea_product_ranked.csv'
    elif site == 'all':
        allProduct.allProductSearch(searchInput)
        csvName = 'all_product_ranked.csv'
    else:
        return render_template("home.html", productList=[])

    productList = loadProducts(csvName)
    return render_template("home.html", productList=productList)

if __name__=="__main__":
    app.run(host="0.0.0.0")