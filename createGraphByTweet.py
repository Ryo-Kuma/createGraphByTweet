import tweetCollector as tc
import createGraphByCsv as cg

# 河野太郎
konotaro = "konotarogomame"

# 処理実行
csvFile = tc.writeCSVfromTweet(konotaro)
cg.createGraph(csvFile)

# おわり！
print("おわり！")
