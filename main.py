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
        raise Exception(f"本日（{target_text}）のリンクがありません。サイト更新前です。")
        
    latest_url = urljoin(LIST_URL, latest_link_tag['href'])

    res_detail = requests.get(latest_url)
    res_detail.raise_for_status()
    soup_detail = BeautifulSoup(res_detail.content, 'html.parser')
    
    # --- 修正ポイント: 画像の「ファイルサイズ」で盤面図を論理的に特定する ---
    best_img_data = None
    max_size = 0
    best_ext = 'jpeg'
    
    # 本文エリア内、または見出し以降の画像を最大15枚リストアップ
    target_images = soup_detail.select('article img, main img, .postBody img, .text img, .pageContents img')
    if not target_images:
        heading_tag = soup_detail.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and target_text in tag.get_text())
        if heading_tag:
            target_images = heading_tag.find_all_next('img', limit=15)

    if not target_images:
        raise Exception("ページ内に画像が見つかりませんでした。")

    # リストアップした画像を順番に確認し、最もデータサイズが大きいものを「盤面」とする
    for img in target_images:
        src = img.get('src', '').lower()
        if any(x in src for x in ['icon', 'banner', 'logo', 'btn', 'share', 'sns', 'thumb']):
            continue
            
        img_url = urljoin(latest_url, img.get('src', ''))
        try:
            res_img = requests.get(img_url, timeout=5)
            res_img.raise_for_status()
            size = len(res_img.content)
            
            # 最大サイズを更新した場合のみ保持
            if size > max_size:
                max_size = size
                best_img_data = res_img.content
                ext = img_url.split('.')[-1][:3]
                best_ext = 'png' if 'png' in ext.lower() else 'jpeg'
        except:
            continue
            
    if not best_img_data:
        raise Exception("画像のダウンロードに失敗したか、有効な画像がありませんでした。")

    # メール送信
    msg = EmailMessage()
    msg['Subject'] = f"【まいにち詰将棋】{target_text}の問題"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg.set_content(f"本日の詰将棋です。\n\n出題元ページ: {latest_url}")
    
    msg.add_attachment(best_img_data, maintype='image', subtype=best_ext, filename=f"tsume_shogi_{today.strftime('%Y%m%d')}.{best_ext}")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
        smtp.send_message(msg)

    print(f"{target_text}の送信完了（画像サイズ: {max_size} bytes）")

if __name__ == "__main__":
    main()
