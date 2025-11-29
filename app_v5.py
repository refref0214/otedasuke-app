import streamlit as st
import pandas as pd
from datetime import date, datetime
import calendar
import gspread
import os
import json # これを追加！

# --- 設定エリア ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# ファイル名を 'secrets.json' に戻したならここも直してね
JSON_FILE = os.path.join(current_dir, 'secrets.json') 

# 【重要】ここにさっきコピーしたIDを貼る！
SPREADSHEET_ID = '1gPO7d5vGegHCR3VKs0xh6z_lgUvh5_7f6nyErfIlE6o' 

MENU = {
    "お皿洗い": 300,
    "洗濯物片付け":300,
    "お風呂掃除": 100,
    "ゴミ出し": 100,
    "玄関掃除": 100,
    "スペシャル手伝い": 500
}
# -----------------

# --- Googleスプレッドシートに接続する関数 ---
def get_worksheet():
    # 1. まずパソコン内に 'secrets.json' があるか探す（家で動かす用）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, 'secrets.json')
    
    if os.path.exists(json_path):
        # ファイルがあればそれを使う
        gc = gspread.service_account(filename=json_path)
    else:
        # 2. ファイルがないなら、クラウドの「秘密のポケット(st.secrets)」を見る
        # （これからクラウド上で設定するやつです）
        if "gcp_service_account" in st.secrets:
            dict_creds = dict(st.secrets["gcp_service_account"])
            gc = gspread.service_account_from_dict(dict_creds)
        else:
            st.error("鍵が見つかりません！secrets.jsonを置くか、クラウドのSecretsを設定してください。")
            return None

    # ID指定で開く
    sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

st.title("💰 お手伝い貯金アプリ Cloud")

# ...（ここから下のコードは今までと同じでOK！）...
# 1. 入力フォーム
st.subheader("📝 記録する")
col1, col2 = st.columns(2)
with col1:
    input_date = st.date_input("日付", date.today())
with col2:
    input_chore = st.selectbox("何をした？", list(MENU.keys()))

if st.button("記録する！"):
    price = MENU[input_chore]
    try:
        sheet = get_worksheet()
        sheet.append_row([str(input_date), input_chore, price])
        st.success(f"「{input_chore}（{price}円）」をクラウドに保存したよ！")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

st.markdown("---")

try:
    sheet = get_worksheet()
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    if not df.empty:
        df['日付'] = pd.to_datetime(df['日付'])

        st.sidebar.header("📅 表示設定")
        df['年月'] = df['日付'].dt.strftime('%Y年%m月')
        month_list = sorted(df['年月'].unique(), reverse=True)
        
        if len(month_list) > 0:
            selected_month = st.sidebar.selectbox("月を選んでね", month_list)
            monthly_df = df[df['年月'] == selected_month]

            st.subheader(f"📊 {selected_month} の成績表")

            total_month = monthly_df['金額'].sum()
            st.metric(label="今月のおこづかい合計", value=f"¥{total_month:,}")

            daily_chart = monthly_df.groupby('日付')['金額'].sum()
            y_m_obj = datetime.strptime(selected_month, '%Y年%m月')
            last_day = calendar.monthrange(y_m_obj.year, y_m_obj.month)[1]
            all_days = pd.date_range(start=f"{y_m_obj.year}-{y_m_obj.month}-01", end=f"{y_m_obj.year}-{y_m_obj.month}-{last_day}", freq='D')
            daily_chart = daily_chart.reindex(all_days, fill_value=0)
            daily_chart.index = daily_chart.index.strftime('%d日')
            
            st.bar_chart(daily_chart)

            with st.expander("詳しい履歴を見る"):
                display_df = monthly_df.copy()
                display_df['日付'] = display_df['日付'].dt.strftime('%Y/%m/%d')
                st.table(display_df[['日付', '内容', '金額']].sort_values('日付', ascending=False))
        else:
            st.info("データはあるけど、日付が正しくないかも？")
    else:
        st.info("まだデータがないよ。スプレッドシートは空っぽです。")

except Exception as e:
    st.error(f"データの読み込みに失敗しました: {e}")