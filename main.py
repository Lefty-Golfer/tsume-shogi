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

    # 日本時間の取得
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

    # --- 修正ポイント: 記事本文エリアの特定と画像抽出の確実化 ---
    res_detail = requests.get(latest_url)
    res_detail.raise_for_status()
    soup_detail = BeautifulSoup(res_detail.content, 'html.parser')
    
    img_tag = None
    
    # 1. 「〇年〇月〇日の詰将棋」というテキストを含む見出しタグ(h1〜h6)を正確に探す
    heading_tag = soup_detail.find(lambda tag: tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and target_text in tag.get_text())
    
    if heading_tag:
        # 見出しが見つかった場合、その直後にある本文画像を抽出
        for img in heading_tag.find_all_next('img'):
            src = img.get('src', '').lower()
            # ヘッダー/サイドバー等の不要な画像（アイコン、バナー等）を除外
            if any(x in src for x in ['icon', 'banner', 'logo', 'btn', 'share', 'sns']):
                continue
            img_tag = img
            break
            
    # 2. 見出しが見つからなかった場合の予備手段（本文領域を直接指定）
    if not img_tag:
        main_areas = soup_detail.select('article, main, .postBody, .text, .contents, #main')
        for area in main_areas:
            for img in area.find_all('img'):
                src = img.get('src', '').lower()
                if any(x in src for x in ['icon', 'banner', 'logo', 'btn', 'share', 'sns']):
                    continue
                img_tag = img
                break
            if img_tag:
                break
        
    if not img_tag or not img_tag.get('src'):
        raise Exception("本文内に盤面画像が見つかりませんでした。")
        
    img_url = urljoin(latest_url, img_tag['src'])

    res_img = requests.get(img_url)
    res_img.raise_for_status()
    img_data = res_img.content

    # メール送信
    msg = EmailMessage()
    msg['Subject'] = f"【まいにち詰将棋】{target_text}の問題"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = EMAIL_ADDRESS
    msg.set_content(f"本日の詰将棋です。\n\n出題元ページ: {latest_url}")
    
    ext = img_url.split('.')[-1][:3]
    subtype = 'png' if 'png' in ext.lower() else 'jpeg'
    msg.add_attachment(img_data, maintype='image', subtype=subtype, filename=f"tsume_shogi_{today.strftime('%Y%m%d')}.{subtype}")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, APP_PASSWORD)
        smtp.send_message(msg)

    print(f"{target_text}の画像の抽出およびメール送信が完了しました。")

if __name__ == "__main__":
    main()
