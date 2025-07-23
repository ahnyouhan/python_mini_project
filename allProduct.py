import threading
import metree
import monster
import health
import pandas as pd

def allProductSearch(inputData):
    t1 = threading.Thread(target=metree.metree_search, args=(inputData,))
    t2 = threading.Thread(target=monster.monster_search, args=(inputData,))
    t3 = threading.Thread(target=health.health_search, args=(inputData,))

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()
    
    csv1 = pd.read_csv('metree_product_ranked.csv')
    csv2 = pd.read_csv('monster_product_ranked.csv')
    csv3 = pd.read_csv('healthkorea_product_ranked.csv')

    csvAll = pd.concat([csv1, csv2, csv3], ignore_index=True)
    csvAll = csvAll.sort_values(by='최종 점수', ascending=False) # 내림차순임 True로하면 오름차순
    csvAll.to_csv('all_product_ranked.csv', index=False, encoding='utf-8-sig')
