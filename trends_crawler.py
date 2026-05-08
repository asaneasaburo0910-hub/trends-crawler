from pytrends.request import TrendReq
import csv
import os
from datetime import datetime
import time

# ============================
# 設定
# ============================
GEO = "JP"  # 日本
OUTPUT_FILE = "trends.csv"

# 調べるキーワードグループ（5個以内で1グループ）
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
    """今日の急上昇ワードを取得"""
    pytrends = TrendReq(hl="ja-JP", tz=540)
    try:
        df = pytrends.trending_searches(pn="japan")
        results = []
        for i, row in enumerate(df[0].tolist()[:20], 1):
            results.append({
                "type": "急上昇ワード",
                "label": "総合",
                "keyword": row,
                "score": 20 - i + 1,  # 順位を逆数でスコア化
                "rank": i,
                "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
        print(f"✅ 急上昇ワード: {len(results)}件取得")
        return results
    except Exception as e:
        print(f"❌ 急上昇ワード取得失敗: {e}")
        return []


def fetch_interest_by_keyword(group):
    """キーワードグループの人気度を取得"""
    pytrends = TrendReq(hl="ja-JP", tz=540)
    results = []
    try:
        pytrends.build_payload(
            group["keywords"],
            cat=0,
            timeframe="now 7-d",  # 直近7日間
            geo=GEO,
        )
        df = pytrends.interest_over_time()
        if df.empty:
            return results

        # 各キーワードの平均スコアを計算
        for keyword in group["keywords"]:
            if keyword in df.columns:
                avg_score = int(df[keyword].mean())
                results.append({
                    "type": "キーワード人気度",
                    "label": group["label"],
                    "keyword": keyword,
                    "score": avg_score,
                    "rank": 0,  # 後でソート
                    "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })

        # スコア順にランク付け
        results.sort(key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(results, 1):
            r["rank"] = i

        print(f"✅ {group['label']}: {len(results)}件取得")
        time.sleep(2)  # APIへの負荷を減らすため少し待つ

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

    # 急上昇ワード取得
    trending = fetch_trending_searches()
    all_results.extend(trending)

    # キーワードグループごとの人気度取得
    for group in KEYWORD_GROUPS:
        items = fetch_interest_by_keyword(group)
        all_results.extend(items)

    save_csv(all_results)

    # 上位5件表示
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
