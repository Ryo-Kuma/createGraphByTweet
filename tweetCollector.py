# coding: UTF-8
import requests
from bs4 import BeautifulSoup
import csv
import sys
import time

from datetime import datetime
#
# 指定されたTwitterのユーザー名のTweetを収集するクラス
# - collectTweet でインスタンスにTweetデータを保持
# - writeCSV で保持したTweetデータをCSVファイルとして保存
#
# cited from https://qiita.com/katz_PG/items/a95a0f91705f80ffc47c
#
class TweetCollector:
    #Twitterの取得URL
    __TWITTER_URL = (
        "https://twitter.com/i/profiles/show/"
        "%(user_name)s/timeline/tweets?include_available_features=1&include_entities=1"
        "%(max_position)s&reset_error_state=false"
    )

    __user_name = ""    #取得するTwitterのユーザー名
    __tweet_data = []   #Tweetのブロックごと配列

    #
    # コンストラクタ
    #
    def __init__(self, user_name):
        self.__user_name = user_name

        #項目名の設定
        row = [
            "ツイートID",
            "名前",
            "ユーザー名",
            "投稿日",
            "本文",
            "返信数",
            "リツイート数",
            "いいね数"
        ]
        self.__tweet_data.append(row)

    #
    # Tweetの収集を開始する
    #
    def collectTweet(self):
        self.nextTweet(0)

    #
    # 指定されたポジションを元に次のTweetを収集する
    #
    def nextTweet(self, max_position):
        # max_position に 0 が指定されていたらポジション送信値なし
        if max_position == 0:
            param_position = ""
        else:
            param_position = "&max_position=" + max_position

        # 指定パラメータをTwitterのURLに入れる
        url = self.__TWITTER_URL % {
            'user_name': self.__user_name,
            'max_position': param_position
        }

        # HTMLをスクレイピングして、Tweetを配列として格納
        res = requests.get(url)
        soup = BeautifulSoup(res.json()["items_html"], "html.parser")

        items = soup.select(".js-stream-item")

        for item in items:
            row = []
            row.append(item.get("data-item-id")) #ツイートID
            row.append(item.select_one(".fullname").get_text().encode("cp932", "ignore").decode("cp932")) #名前
            row.append(item.select_one(".username").get_text()) #ユーザー名
            row.append(item.select_one("._timestamp").get_text()) #投稿日
            row.append(item.select_one(".js-tweet-text-container").get_text().strip().encode("cp932", "ignore").decode("cp932")) #本文
            row.append(item.select(".ProfileTweet-actionCountForPresentation")[0].get_text()) #返信カウント
            row.append(item.select(".ProfileTweet-actionCountForPresentation")[1].get_text()) #リツイートカウント
            row.append(item.select(".ProfileTweet-actionCountForPresentation")[3].get_text()) #いいねカウント

            self.__tweet_data.append(row)

        print(str(max_position) + "取得完了")
        time.sleep(2) #負荷かけないように

        # ツイートがまだあれば再帰処理
        if res.json()["min_position"] is not None:
            self.nextTweet(res.json()["min_position"])

    #
    # 取得したTweetをCSVとして書き出す
    #
    def writeCSV(self):
        today = datetime.now().strftime("%Y%m%d%H%M")
        file = "./csv/" + self.__user_name + "-" + today + ".csv"
        with open(file, "w") as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerows(self.__tweet_data)
        print("csv出力完了" )
        return file

#
# ツイート収集
#
def writeCSVfromTweet(user_name):
    twc = TweetCollector(user_name) #Twitterのユーザー名を指定
    twc.collectTweet()
    file = twc.writeCSV()
    return file

if __name__ == "__main__":
    if len(sys.argv) != 2 :
        print("param error!")
        sys.exit()
    writeCSVfromTweet(sys.argv[1])
else:
    print("いんぽーと!:tweetCollector.py")
