import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
from urllib.parse import urljoin
from datetime import datetime, timedelta, timezone

def main():
    EMAIL_ADDRESS = "express.t.ogino@gmail.com"
    APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD") 
    
    if not APP_PASSWORD:
        raise ValueError("環境変数 'GMAIL_APP_PASSWORD' が設定されていません。")

    LIST_URL = "https://www.shogi.or.jp/tsume_shogi/everyday/"

    JST = timezone(timedelta(hours=+9), 'JST')
    today = datetime.now(JST)
    target_text = f"{today.year}年{today.month}月{today.day}日の詰将棋"

    res_list = requests.get(LIST_URL)
    res_list.raise_for_status()
    soup_list = BeautifulSoup(res_list.content, 'html.parser')
    
    latest_link_tag = None
    for a in soup_list.find_all('a'):
        if a.text and target_text in a.text:
            latest_link_tag = a
            break

    if not latest_link_tag:
        raise Exception(f"本日（{target_text}）のリンクがありません。")
        
    latest_url = urljoin(LIST_URL, latest_link_tag['href'])

    res_detail = requests.get(latest_url)
    res_detail.raise_for_status()
    soup_detail = BeautifulSoup(res_detail.content, 'html.parser')
    
    # ページ内のすべての画像を抽出
    all_imgs = soup_detail.find_all('img')
    img_urls = []
    for i, img in enumerate(all_imgs, 1):
        src = img.get('src')
        if src:
            absolute_url = urljoin(latest_url, src)
            img_urls.append(f"{i}. {absolute_url}")
            
    if not img_urls:
        raise Exception("ページ内に画像が一つも見つかりませんでした。")

    # URLリストをメールで送信
    msg = EmailMessage()
    msg['Subject'] = "【調査用】ページ内の全画像URLリスト"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    
    body_text = f"出題元ページ: {latest_url}\n\nページ内の全画像URLです。クリックして正解の盤面があるか確認してください。\n\n"
    body_text += "\n".join(img_urls)
    msg.set_content(body_text)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
        smtp.send_message(msg)

    print("調査用メールの送信が完了しました。")

if __name__ == "__main__":
    main()
