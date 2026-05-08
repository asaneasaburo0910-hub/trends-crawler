import requests
import csv
import os
from datetime import datetime

# ============================
# 設定
# ============================
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")  # GitHubのSecretsから自動取得
OUTPUT_FILE = "trends.csv"

KEYWORD_GROUPS = [
    {
        "label": "エンタメ・ゲーム",
        "keywords": ["ゲーム", "アニメ", "映画", "Netflix", "Steam"]
    },
    {
        "label": "ビジネス・投資",
        "keywords": ["株", "投資", "副業", "NISA", "仮想通貨"]
    },
]


def fetch_trending_searches():
    """日本の急上昇ワードを取得"""
    results = []
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_trends_trending_now",
            "frequency": "daily",
            "geo": "JP",
            "hl": "ja",
            "api_key": SERPAPI_KEY,
        }
        res = requests.get(url, params=params, timeout=15)
        data = res.json()

        searches = data.get("daily_searches", [])
        if searches:
            latest = searches[0].get("searches", [])
            for i, item in enumerate(latest[:20], 1):
                results.append({
                    "type": "急上昇ワード",
                    "label": "総合",
                    "keyword": item.get("query", ""),
                    "score": item.get("traffic", 0),
                    "rank": i,
                    "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })

        print(f"✅ 急上昇ワード: {len(results)}件取得")

    except Exception as e:
        print(f"❌ 急上昇ワード取得失敗: {e}")

    return results


def fetch_keyword_interest(group):
    """キーワードグループの人気度を取得"""
    results = []
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_trends",
            "q": ",".join(group["keywords"]),
            "geo": "JP",
            "date": "now 7-d",
            "api_key": SERPAPI_KEY,
        }
        res = requests.get(url, params=params, timeout=15)
        data = res.json()

        timeline = data.get("interest_over_time", {}).get("timeline_data", [])
        if not timeline:
            print(f"⚠️ {group['label']}: データなし")
            return results

        # 各キーワードの平均スコアを計算
        scores = {kw: [] for kw in group["keywords"]}
        for point in timeline:
            for val in point.get("values", []):
                kw = val.get("query")
                if kw in scores:
                    scores[kw].append(val.get("extracted_value", 0))

        for kw, vals in scores.items():
            avg = int(sum(vals) / len(vals)) if vals else 0
            results.append({
                "type": "キーワード人気度",
                "label": group["label"],
                "keyword": kw,
                "score": avg,
                "rank": 0,
                "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(results, 1):
            r["rank"] = i

        print(f"✅ {group['label']}: {len(results)}件取得")

    except Exception as e:
        print(f"❌ {group['label']} 取得失敗: {e}")

    return results


def save_csv(items):
    """結果をCSVに保存（追記モード）"""
    file_exists = os.path.exists(OUTPUT_FILE)
    fieldnames = ["type", "label", "keyword", "score", "rank", "fetched_at"]

    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(items)

    print(f"💾 {OUTPUT_FILE} に {len(items)}件保存しました")


def main():
    print(f"🚀 Googleトレンド収集開始: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    all_results = []

    trending = fetch_trending_searches()
    all_results.extend(trending)

    for group in KEYWORD_GROUPS:
        items = fetch_keyword_interest(group)
        all_results.extend(items)

    save_csv(all_results)

    print("\n📊 急上昇ワード トップ5:")
    for item in [i for i in all_results if i["type"] == "急上昇ワード"][:5]:
        print(f"  {item['rank']}. {item['keyword']}")

    for group in KEYWORD_GROUPS:
        print(f"\n📊 {group['label']} 人気度:")
        for item in [i for i in all_results if i["label"] == group["label"]]:
            print(f"  {item['rank']}. {item['keyword']} (スコア: {item['score']})")

    print(f"\n✨ 完了！合計 {len(all_results)} 件")


if __name__ == "__main__":
    main()
