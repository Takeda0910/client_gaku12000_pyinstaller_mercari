import datetime
import eel
import math
import os
import pandas as pd
import time
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

EXP_CSV_PATH="./mercari_{datetime}.csv"
EXP_CSV_PATH_2="./mercari_during_trading_{datetime}.csv"
LOG_FILE_PATH = "./log/log_{datetime}.log"
log_file_path = LOG_FILE_PATH.format(datetime = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')) 
    
### Chromeを起動する関数
def set_driver(driver_path, headless_flg):
    # Chromeドライバーの読み込み
    options = ChromeOptions()

    # ヘッドレスモード（画面非表示モード）をの設定
    if headless_flg == True:
        options.add_argument('--headless')

    # 起動オプションの設定
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36')
    options.add_argument('log-level=3')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    # options.add_argument('--incognito')          # シークレットモードの設定を付与
    options.add_argument('--user-data-dir=' + os.path.join(os.getcwd(),"client_profile"))
    # ChromeのWebDriverオブジェクトを作成する。
    return Chrome(ChromeDriverManager().install(), options=options)
    # return Chrome("./chromedriver", options=options)

driver = set_driver("chromedriver.exe", False)  

def log(txt):
    now = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') 
    logStr = '[%s: %s] %s' % ('log', now, txt)   
    with open(log_file_path, 'a', encoding='utf-8_sig') as f:
        f.write(logStr + '\n')
    print(logStr)   

# 購入済み商品一覧
def crawle_bueid_items(limit:int):    
    driver.get("https://jp.mercari.com/mypage/purchases/completed")
    time.sleep(3)
    click_count = math.ceil((limit-50)/20)
    for i in range(click_count):
        try:
            driver.find_elements_by_css_selector('mer-button button')[-1].click()
            time.sleep(3)
        except Exception as e:
            print(f"see more button not found:{e}")
            break
    item_ids = [elm.get_attribute("href").split("/")[-1] for elm in driver.find_elements_by_css_selector("#my-page-main-content mer-list-item a")]
    item_ids = item_ids[:limit]
    print(len(item_ids))
    eel.view_log_js(f"{len(item_ids)}件のID取得成功")
    
    success = 0
    fail = 0
    count = 1
    items = []
    eel.view_log_js("詳細情報取得開始")
    for item_id in item_ids:
        print(f"item_id: {item_id}")
        try:
            items.append(fetch_buied_item(item_id))   
            eel.view_log_js(f"{count}件目成功")
            log(f"{count}件目成功：{item_id}") 
            success += 1 
        except Exception as e:
            eel.view_log_js(f"{count}件目失敗")
            log(f"{count}件目失敗：{item_id}")
            fail += 1
        finally:
            count += 1 
    log("最終です。終了します。")     
    now = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    df = pd.DataFrame()
    for item in items:
        df = df.append(item, ignore_index=True).fillna("")
    df.to_csv(EXP_CSV_PATH.format(datetime=now), header=["購入日時", "商品名", "価格", "販売者名(URL)", "商品ＩＤ", "商品URL"], encoding="utf-8-sig")
    log(f"処理完了　成功件数： {success} 件 / 失敗件数： {fail} 件")
    #chromeを閉じる
    driver.quit()
    return items

# 購入済み商品詳細   
def fetch_buied_item(item_id: str):
    SOLD_ITEM_URL = "https://jp.mercari.com/transaction/{item_id}"    
    driver.get(SOLD_ITEM_URL.format(item_id=item_id))
    time.sleep(3)    
    # 購入者情報    
    item_name = None
    seller_name_and_url = None
    sold_price = None
    buied_at = None
    item_id_url = None
        
    try:
        try:
            price_elm = driver.find_element_by_xpath("//span[contains(text(), '商品代金')]/following-sibling::span[1]")
            sold_price = int(price_elm.text.replace("¥", "").replace(",", ""))
            print(sold_price)
        except Exception as e:
            print(f"sold price is not found: {e}")

        
        try:
            buied_at_elm = driver.find_element_by_xpath("//span[contains(text(), '購入日時')]/following-sibling::span[1]")
            buied_at = buied_at_elm.text.split()
            buied_at = buied_at[0]
            print(buied_at)
        except Exception as e:
            print(f"buied_at is not found: {e}")
                                            
        
        try: # 2022/0320 読み込み不可になったため変更
            # seller_name = driver.find_element_by_css_selector("#transaction-main-content [data-testid='seller-link']").get_attribute("name")
            seller_name = driver.find_element_by_css_selector(".layout__LayoutCol-sc-1lyi7xi-2.ijeNNK [data-testid='seller-link']").get_attribute("name")
            
            
            # seller_name_url = driver.find_element_by_css_selector("#transaction-main-content a").get_attribute("href")
            seller_name_url = driver.find_element_by_css_selector(".layout__LayoutCol-sc-1lyi7xi-2.ijeNNK a").get_attribute("href")
            
            
            seller_name_and_url = f"{seller_name} ({seller_name_url})"
            print(seller_name_and_url)
        except Exception as e:
            print(f"seller name is not found")
            
        try:
            item_name = driver.find_element_by_css_selector("mer-item-object").text
            print(item_name)
        except Exception as e:
            print(f"item name is not found")

        try:
            # item_id_url = driver.find_element_by_css_selector("#transaction-sidebar mer-list-item a").get_attribute("href")
            item_id_url = driver.find_element_by_css_selector(".StickyNode__SimpleSticky-sc-bomsx6-1.jVOxuG mer-list-item a").get_attribute("href")
            print(f"item_id_url {item_id_url}")
        except Exception as e:
            print(f"item url is not found")      

    except Exception as e:
        print(f"buyer data is not found: {item_id} | {e}")
            
    return dict(
        buied_at = buied_at,
        item_name = item_name,
        sold_price = sold_price,
        seller_name_and_url = seller_name_and_url,
        item_id = item_id,
        item_id_url = item_id_url
    )

############################################  
# 取引中商品一覧
def crawle_bueid_items_2(limit:int):    
    driver.get("https://jp.mercari.com/mypage/purchases")
    time.sleep(3)
    click_count = math.ceil((limit-50)/20)
    for i in range(click_count):
        try:
            driver.find_elements_by_css_selector('mer-button button')[-1].click()
            time.sleep(3)
        except Exception as e:
            print(f"see more button not found:{e}")
            break
    item_ids = [elm.get_attribute("href").split("/")[-1] for elm in driver.find_elements_by_css_selector("#my-page-main-content mer-list-item a")]
    item_ids = item_ids[:limit]
    print(len(item_ids))
    eel.view_log_js(f"{len(item_ids)}件のID取得成功")
    
    success = 0
    fail = 0
    count = 1
    items = []
    eel.view_log_js("詳細情報取得開始")
    for item_id in item_ids:
        print(f"item_id: {item_id}")
        try:
            items.append(fetch_buied_item(item_id))   
            eel.view_log_js(f"{count}件目成功")
            log(f"{count}件目成功：{item_id}") 
            success += 1 
        except Exception as e:
            eel.view_log_js(f"{count}件目失敗")
            log(f"{count}件目失敗：{item_id}")
            fail += 1
        finally:
            count += 1 
    log("最終です。終了します。")     
    now = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    df = pd.DataFrame()
    for item in items:
        df = df.append(item, ignore_index=True).fillna("")
    df.to_csv(EXP_CSV_PATH_2.format(datetime=now), header=["購入日時", "商品名", "価格", "販売者名(URL)", "商品ＩＤ", "商品URL"], encoding="utf-8-sig")
    log(f"処理完了　成功件数： {success} 件 / 失敗件数： {fail} 件")
    #chromeを閉じる
    driver.quit()
    return items

# 取引中商品詳細   
def fetch_buied_item_2(item_id: str):
    SOLD_ITEM_URL = "https://jp.mercari.com/transaction/{item_id}"    
    driver.get(SOLD_ITEM_URL.format(item_id=item_id))
    time.sleep(3)    
    # 購入者情報    
    item_name = None
    seller_name_and_url = None
    sold_price = None
    buied_at = None
    item_id_url = None
        
    try:
        try:
            price_elm = driver.find_element_by_xpath("//span[contains(text(), '商品代金')]/following-sibling::span[1]")
            sold_price = int(price_elm.text.replace("¥", "").replace(",", ""))
            print(sold_price)
        except Exception as e:
            print(f"sold price is not found: {e}")

        try:
            buied_at_elm = driver.find_element_by_xpath("//span[contains(text(), '購入日時')]/following-sibling::span[1]")
            buied_at = buied_at_elm.text.split()
            buied_at = buied_at[0]
            print(buied_at)
        except Exception as e:
            print(f"buied_at is not found: {e}")
                                            
        
        try:
            # seller_name = driver.find_element_by_css_selector("#transaction-main-content [data-testid='seller-link']").get_attribute("name")
            seller_name = driver.find_element_by_css_selector(".layout__LayoutCol-sc-1lyi7xi-2.ijeNNK [data-testid='seller-link']").get_attribute("name")
            
            # seller_name_url = driver.find_element_by_css_selector("#transaction-main-content a").get_attribute("href")
            seller_name_url = driver.find_element_by_css_selector(".layout__LayoutCol-sc-1lyi7xi-2.ijeNNK a").get_attribute("href")
            
            seller_name_and_url = f"{seller_name} ({seller_name_url})"
            print(seller_name_and_url)
        except Exception as e:
            print(f"seller name is not found")
            
        try:
            item_name = driver.find_element_by_css_selector("mer-item-object").text
            print(item_name)
        except Exception as e:
            print(f"item name is not found")

        try:
            # item_id_url = driver.find_element_by_css_selector("#transaction-sidebar mer-list-item a").get_attribute("href")
            item_id_url = driver.find_element_by_css_selector(".StickyNode__SimpleSticky-sc-bomsx6-1.jVOxuG mer-list-item a").get_attribute("href")
            print(f"item_id_url {item_id_url}")
        except Exception as e:
            print(f"item name is not found")      

    except Exception as e:
        print(f"buyer data is not found: {item_id} | {e}")
            
    return dict(
        buied_at = buied_at,
        item_name = item_name,
        sold_price = sold_price,
        seller_name_and_url = seller_name_and_url,
        item_id = item_id,
        item_id_url = item_id_url
    )

############################################
def main(id_count):
    int_id_count = int(id_count)
    crawle_bueid_items(int_id_count)

def main_2(id_count):
    int_id_count = int(id_count)
    crawle_bueid_items_2(int_id_count)



# if __name__ == "__main__":
#     main()      

