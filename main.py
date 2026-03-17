import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage

def main():
    # --- 1. 設定 ---
    EMAIL_ADDRESS = "express.t.ogino@gmail.com"
    # ※ セキュリティのため、環境変数からGmailのアプリパスワードを取得します
    APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") 
    
    if not APP_PASSWORD:
        raise ValueError("環境変数 'GMAIL_APP_PASSWORD' が設定されていません。")

    BASE_URL = "https://www.shogi.or.jp"
    LIST_URL = "https://www.shogi.or.jp/tsume_shogi/everyday/"

    # --- 2. 最新の詰将棋ページのURLを取得 ---
    res_list = requests.get(LIST_URL)
    res_list.raise_for_status()
    soup_list = BeautifulSoup(res_list.content, 'html.parser')
    
    # 最新の記事リンクを取得
    latest_link_tag = soup_list.select_one('a[href^="/tsume_shogi/everyday/20"]')
    if not latest_link_tag:
        raise Exception("最新の詰将棋リンクが見つかりませんでした。")
        
    latest_url = BASE_URL + latest_link_tag['href']

    # --- 3. 詰将棋ページから画像を抽出してダウンロード ---
    res_detail = requests.get(latest_url)
    res_detail.raise_for_status()
    soup_detail = BeautifulSoup(res_detail.content, 'html.parser')
    
    # 盤面画像を抽出（メインコンテンツ内の最初の画像）
    img_tag = soup_detail.select_one('main img, .contents img, article img')
        
    if not img_tag or not img_tag.get('src'):
        raise Exception("画像が見つかりませんでした。")
        
    img_url = img_tag['src']
    if not img_url.startswith("http"):
        img_url = BASE_URL + img_url

    res_img = requests.get(img_url)
    res_img.raise_for_status()
    img_data = res_img.content

    # --- 4. メール送信 ---
    msg = EmailMessage()
    msg['Subject'] = "【まいにち詰将棋】本日の問題"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg.set_content(f"本日の詰将棋です。\n\n出題元ページ: {latest_url}")
    
    # 画像を添付
    ext = img_url.split('.')[-1][:3]
    subtype = 'png' if 'png' in ext.lower() else 'jpeg'
    msg.add_attachment(img_data, maintype='image', subtype=subtype, filename=f"tsume_shogi.{subtype}")

    # SMTPサーバー経由で送信 (Gmail)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
        smtp.send_message(msg)

    print("詰将棋のメール送信が完了しました。")

if __name__ == "__main__":
    main()
