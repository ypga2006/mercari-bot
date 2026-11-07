import os
import time
import requests
import re
import json

TARGET_URLS = [
    {
        "name": "슈퍼소니코",
        "url": "https://irasshaimase.co.kr/mercari.s/https://jp.mercari.com/search?keyword=%E3%81%99%E3%83%BC%E3%81%B1%E3%83%BC%E3%81%9D%E3%81%AB%E5%AD%90",
    },
    {
        "name": "범용 토끼 하츠네미쿠",
        "url": "https://irasshaimase.co.kr/mercari.s/https://jp.mercari.com/search?keyword=%E6%B1%8E%E7%94%A8%E3%81%86%E3%81%95%E3%81%8E%20%E5%88%9D%E9%9F%B3%E3%83%9F%E3%82%AF",
    },
    {
        "name": "마메고마",
        "url": "https://irasshaimase.co.kr/mercari.s/https://jp.mercari.com/search?keyword=%E3%81%BE%E3%82%81%E3%82%B4%E3%83%9E%20%E3%81%AC%E3%81%84%E3%81%90%E3%82%8B%E3%81%BF",
    },
]

# 🔗 디스코드 웹훅 URL을 코드 내에 직접 설정했습니다.
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1568541299420958790/gT5Z8R7LAj2_LPbBSEbN0ibNo8K3Dtw7QI60ERR7u9jcdKQxc2cAeRabeGJDzlqVzgho"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "latest_item_cache.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# 🚀 Session 객체를 생성하여 TCP 연결을 재사용하고 속도를 높입니다.
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def get_item_ids(target_url):
    try:
        # 🚀 timeout을 10초로 설정하여 속도를 최적화했습니다.
        response = SESSION.get(target_url, timeout=10)
        response.raise_for_status()
        found_ids = re.findall(r"https://jp\.mercari\.com/item/(m\d+)", response.text)
        
        seen = set()
        item_ids = []
        for item_id in found_ids:
            if item_id not in seen:
                seen.add(item_id)
                item_ids.append(item_id)
            if len(item_ids) >= 10:
                break
        return item_ids
    except Exception as e:
        print(f"오류 발생 ({target_url}): {e}")
        return []

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache_data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"캐시 저장 오류: {e}")

def send_discord_alert(name, new_items):
    if not DISCORD_WEBHOOK_URL:
        print("디스코드 웹훅 URL이 설정되지 않았습니다.")
        return

    content = f"🚨 **[{name}] 새로운 상품 {len(new_items)}건 발견!**\n"
    for item in new_items:
        content += f"- 상품 링크: {item['item_url']}\n- 구매대행: {item['proxy_url']}\n"

    try:
        SESSION.post(DISCORD_WEBHOOK_URL, json={"content": content}, timeout=10)
    except Exception as e:
        print(f"디스코드 전송 오류: {e}")

def main():
    cache = load_cache()
    is_updated = False

    for target in TARGET_URLS:
        name = target["name"]
        url = target["url"]

        current_ids = get_item_ids(url)
        if not current_ids:
            continue

        current_top_id = current_ids[0]
        previous_top_id = cache.get(name)

        if not previous_top_id:
            cache[name] = current_top_id
            is_updated = True
            print(f"[{name}] 초기 최신 ID 저장: {current_top_id}")
        elif current_top_id != previous_top_id:
            print(f"[{name}] 새 상품 감지!")
            new_ids = []
            for item_id in current_ids:
                if item_id == previous_top_id:
                    break
                new_ids.append(item_id)
            
            if not new_ids:
                new_ids = [current_top_id]

            new_items_data = []
            for item_id in reversed(new_ids):
                item_url = f"https://jp.mercari.com/item/{item_id}"
                proxy_url = f"https://irasshaimase.co.kr/mercari/bid.s/{item_url}"
                new_items_data.append({"item_url": item_url, "proxy_url": proxy_url})

            send_discord_alert(name, new_items_data)
            cache[name] = current_top_id
            is_updated = True

    if is_updated:
        save_cache(cache)

if __name__ == "__main__":
    main()
