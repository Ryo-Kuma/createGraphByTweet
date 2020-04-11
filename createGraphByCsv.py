import sys
import pandas as pd
import numpy as np
from fbprophet import Prophet
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
import datetime

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime as dtm

#
# csvファイルを読み込んで感染者推移のグラフを作成する
#
def createGraph(file_name):
    # 作成するグラフのサイズ・フォント等設定
    plt.rcParams["figure.autolayout"] = True
    plt.rcParams["figure.figsize"] = [16.0, 9.0]
    plt.rcParams["grid.linewidth"] = 0.5
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Hiragino Maru Gothic Pro', 'Yu Gothic',\
                                       'Meirio', 'Takao', 'Noto Sans CJK JP',\
                                       'VL PGothic', 'IPAexGothic', 'IPAPGothic']

    # csvを読み込み、該当データのみ抽出
    csv_input = pd.read_csv(filepath_or_buffer=file_name, encoding="ms932", sep=",")
    csv_input = csv_input.loc[:,["本文"]]
    csv_input = csv_input.query('本文.str.contains("国内感染者", na=False)', engine='python')
    csv_input = csv_input[::-1]

    # データ変換
    date_list = list() # 日付
    infected_list = list() # 感染者
    new_infected_list = list() # 新規感染者
    recovery_list = list() # 退院
    new_recovery_list = list() # 新規退院者
    hospitalized_list = list() # 入院中
    new_hospitalized_list = list() # 新規入院者
    keisho_list = list() # 軽中度・無症状
    new_keisho_list = list() # 新規軽中度・無症状
    ICU_list = list() # 人工呼吸/ICU
    new_ICU_list = list() # 新規人工呼吸/ICU
    death_list = list() # 死者
    new_death_list = list() # 新規死者

    for row in csv_input.itertuples():
        for state in row.本文.splitlines():
            state = state.strip("名。").strip()
            if "クルーズ" in state:
                break
            elif "新たに" in state:
                continue
            elif "となりました" in state:
                continue
            elif "日" in state:
                if len(state) < 11:
                    state = state[:state.index("日")+1]
                    date_list.append(state)
            elif "国内感染者" in state:
                infected = int(state.strip("国内感染者"))
                addList(infected, infected_list, new_infected_list, date_list, 24)
            elif "退院" in state:
                recovery = int(state.strip("退院"))
                addList(recovery, recovery_list, new_recovery_list, date_list)
            elif "入院中" in state:
                hospitalized = int(state.strip("入院中"))
                addList(hospitalized, hospitalized_list, new_hospitalized_list, date_list, 24)
            elif "軽中度" in state:
                keisho = int(state.strip("軽中度・無症状"))
                addList(keisho, keisho_list, new_keisho_list, date_list, 19)
            elif "陽性" in state:
                if "陽性だが症状未確認" in state:
                    continue
                mushojo = int(state.strip("陽性無症状入院").strip("陽性で症状なし"))
                # "軽中度・無症状"リストに合算
                mushojoA = mushojo + keisho_list.pop()
                del new_keisho_list[-1]
                addList(mushojoA, keisho_list, new_keisho_list, date_list, 19)
                # "入院中"リストに合算
                mushojoB = mushojo + hospitalized_list.pop()
                del new_hospitalized_list[-1]
                addList(mushojoB, hospitalized_list, new_hospitalized_list, date_list, 24)
            elif "症状有無確認中" in state:
                today = getDate(date_list[-1])
                tgt = datetime.datetime(2020, 3, 29, 0, 0)
                if today < tgt:
                    umukakunin = int(state.strip("症状有無確認中"))
                    # "入院中"リストに合算
                    umukakunin += hospitalized_list.pop()
                    del new_hospitalized_list[-1]
                    addList(umukakunin, hospitalized_list, new_hospitalized_list, date_list, 24)
            elif "人工呼吸" in state:
                ICU = int(state.strip("人工呼吸/ICUまたは"))
                addList(ICU, ICU_list, new_ICU_list, date_list)
            elif "死亡" in state:
                death = int(state.strip("死亡"))
                addList(death, death_list, new_death_list, date_list, 1)
                break
            else:
                pass

    # 新規ウィンドウ描画
    fig1 = plt.figure()

    # グラフ1つめ
    ax1 = fig1.add_subplot(1, 2, 1)
    ax1.set_title("コロナの感染者推移 by河野大臣のTwitter")
    ax1.plot(date_list, infected_list, marker="o", color="tab:blue", label="国内感染者", linestyle="-")
    ax1.plot(date_list, hospitalized_list, marker="d", color="tab:green", label="入院中", linestyle="-")
    ax1.plot(date_list, keisho_list, marker="+", color="c", label="軽中度・無症状", linestyle="-")
    ax1.plot(date_list, recovery_list, marker="^", color="tab:orange", label="退院", linestyle="-")
    ax1.plot(date_list, ICU_list, marker="*", color="m", label="人工呼吸/ICU", linestyle="-")
    ax1.plot(date_list, death_list, marker="v", color="tab:red", label="死亡", linestyle="-")
    ax1.legend(loc="upper left")
    ax1.grid(which="both")
    ax1.set_yscale('log')
    ax1.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    plt.xticks(date_list, date_list, rotation="vertical")

    # グラフ2つめ
    ax2 = fig1.add_subplot(1, 2, 2)
    ax2.set_title("(線形目盛)")
    ax2.plot(date_list, infected_list, marker="o", color="tab:blue", label="国内感染者", linestyle="-")
    ax2.plot(date_list, hospitalized_list, marker="d", color="tab:green", label="入院中", linestyle="-")
    ax2.plot(date_list, keisho_list, marker="+", color="c", label="軽中度・無症状", linestyle="-")
    ax2.plot(date_list, recovery_list, marker="^", color="tab:orange", label="退院", linestyle="-")
    ax2.plot(date_list, ICU_list, marker="*", color="m", label="人工呼吸/ICU", linestyle="-")
    ax2.plot(date_list, death_list, marker="v", color="tab:red", label="死亡", linestyle="-")
    ax2.grid(True)
    plt.xticks(date_list, date_list, rotation="vertical")

    # グラフ保存
    plt.savefig("./png/" + dtm.now().strftime("%Y%m%d") + "_01_total.png")

    # 新規ウィンドウ描画
    fig2 = plt.figure()

    # グラフ3つめ
    ax3 = fig2.add_subplot(1, 2, 1)
    ax3.set_title("前日１２時時点との差分")
    ax3.plot(date_list, new_infected_list, marker="o", color="tab:blue", label="国内感染者", linestyle=":")
    ax3.plot(date_list, new_hospitalized_list, marker="d", color="tab:green", label="入院中", linestyle=":")
    ax3.plot(date_list, new_keisho_list, marker="+", color="c", label="軽中度・無症状", linestyle=":")
    ax3.plot(date_list, new_recovery_list, marker="^", color="tab:orange", label="退院", linestyle=":")
    ax3.plot(date_list, new_ICU_list, marker="*", color="m", label="人工呼吸/ICU", linestyle=":")
    ax3.plot(date_list, new_death_list, marker="v", color="tab:red", label="死亡", linestyle=":")
    ax3.legend(loc="upper left")
    ax3.grid(True)
    plt.xticks(date_list, date_list, rotation="vertical")

    # グラフ4つめ
    ax4 = fig2.add_subplot(1, 2, 2)
    ax4.set_title("致死率(%)")
    death_rate_list = list()
    for death, infected in zip(death_list, infected_list):
        death_rate = Decimal(str(death / infected)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        death_rate *= 100
        death_rate_list.append(death_rate)
    sp_flu = [1.6]*len(date_list)
    flu = [0.1]*len(date_list)
    ax4.plot(date_list, death_rate_list, marker="8", color="tab:red", label=None, linestyle="-")
    ax4.plot(date_list, sp_flu, marker="None", color="tab:red", label="スペイン風邪(国内) 1.6%", linewidth = 0.8, linestyle="-.")
    ax4.plot(date_list, flu, marker="None", color="tab:red", label="季節性インフルエンザ 0.1%以下", linestyle=":")
    ax4.legend(loc="upper left")
    ax4.grid(True)
    plt.xticks(date_list, date_list, rotation="vertical")

    # グラフ保存
    plt.savefig("./png/" + dtm.now().strftime("%Y%m%d") + "_02_rate.png")

    # 将来予測(グラフ5つめ)
    getYosoData(date_list, infected_list)

#
# 指定のリストに要素を追加する
#
def addList(element, total_list, new_list, date_list, init_num = 0):
    if len(total_list) == 0:
        # 初回のみ実行
        new_list.append(init_num)
    else:
        if date_list[-1] == date_list[-2]:
            # 同日に2回以上ツイートしていた場合の2回目以降
            new_element = new_list[-1]
        elif len(date_list) > 2 and date_list[-2] == date_list[-3]:
            # 同日に2回以上ツイートしていた場合の翌日の1回目
            tmp_date_list = list(date_list)
            del tmp_date_list[-1]
            zip_obj = zip(reversed(tmp_date_list), reversed(list(total_list)))
            last_element = total_list[-1]
            for last_date, last_total in zip_obj:
                if date_list[-2] == last_date:
                    last_element = last_total
                else:
                    break
            new_element = element - last_element
        else:
            # その他の通常ケース
            new_element = element - total_list[-1]
        new_list.append(new_element)
    total_list.append(element)

#
# 全角文字列の日付をyyyy/m/dに変換
#
def getDate(date):
    month = date[:date.index("月")]
    day = date[date.index("月")+1:date.index("日")]
    new_date = "2020/" + str(int(month)) + "/" + str(int(day))
    new_date = datetime.datetime.strptime(new_date, '%Y/%m/%d')
    return new_date

#
# 日付リストと感染者リストから、将来を予測する
#
def getYosoData(date_list, infected_list):
    # 日付変換(M月D日 → yyyy/m/d)
    date_list_yyyymd = list()
    for date in date_list:
        date_list_yyyymd.append(getDate(date))

    # Prophetに学習させるためのデータフレーム作成
    df = pd.DataFrame({"ds": date_list_yyyymd, "y": infected_list})
    df["y"] = np.log(df["y"])

    # モデルを選択し、学習させる
    model = Prophet()
    model.fit(df)

    # 将来予測
    future_data = model.make_future_dataframe(periods=15, freq = 'd')
    forecast_data = model.predict(future_data)

    # logを取って予測した値を真数に戻す
    forecast_data["yhat"] = np.exp(forecast_data["yhat"])
    forecast_data["yhat_lower"] = np.exp(forecast_data["yhat_lower"])
    forecast_data["yhat_upper"] = np.exp(forecast_data["yhat_upper"])

    # グラフ表示
    model.plot(forecast_data)
    plt.title("機械学習で将来予測してみた")
    plt.xlabel(None)
    plt.ylabel(None)

    # グラフ保存
    plt.savefig("./png/" + dtm.now().strftime("%Y%m%d") + "_03_yoso.png")

if __name__ == "__main__":
    if len(sys.argv) != 2 :
        print("param error!")
        sys.exit()
    createGraph("./csv/" + sys.argv[1])
else:
    print("いんぽーと!:createGraphByCsv.py")
