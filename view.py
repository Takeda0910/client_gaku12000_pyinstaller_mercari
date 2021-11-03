import eel
import desktop
# import search
import client_mercari_purchase

app_name="html"
end_point="index.html"
size=(700,600)

@eel.expose
def mercari_scraping():
    eel.view_log_js("開始")
    eel.view_log_js("ID取得中…")
    eel.view_log_js("しばらくお待ち下さい…")
    client_mercari_purchase.main()
    eel.view_log_js("終了")
    
desktop.start(app_name,end_point,size)
#desktop.start(size=size,appName=app_name,endPoint=end_point)
