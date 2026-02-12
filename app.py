import streamlit as st
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Sayfa Ayarları
st.set_page_config(page_title="Wordle by ssxar", page_icon="✍️", layout="centered")

# --- CSS: HELVETICA VE GÖRSEL TASARIM ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; }
    .letter-slot { 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        font-size: 24px; font-weight: bold; border: 2px solid #333; border-radius: 5px; 
        padding: 10px; width: 45px; height: 45px; text-align: center; display: inline-block; margin: 2px; 
    }
    .correct-pos { border-bottom: 5px solid #28a745 !important; background-color: #e6ffed; } 
    .wrong-pos { border-bottom: 5px solid #fd7e14 !important; background-color: #fff5e6; }
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS BAĞLANTISI ---
# Not: st.connection otomatik olarak secrets.toml içindeki URL'yi kullanır.
conn = st.connection("gsheets", type=GSheetsConnection)

def get_leaderboard():
    try:
        return conn.read(worksheet="Sheet1", ttl="0m")
    except:
        return pd.DataFrame(columns=["İsim", "Puan", "Tahmin"])

def save_score(name, score, attempts):
    existing_data = get_leaderboard()
    new_data = pd.DataFrame([{"İsim": name, "Puan": score, "Tahmin": attempts}])
    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
    conn.update(worksheet="Sheet1", data=updated_df)

# --- KELİME HAVUZU ---
TURKISH_WORDS = {
    5: ["KALEM", "KİTAP", "DENİZ", "GÜNEŞ", "SINAV", "BAHAR", "CÜMLE", "DÜNYA", "EĞİTİM", "FİKİR"],
    6: ["TÜRKÇE", "SÖZCÜK", "STATİK", "TASARIM", "MİMARİ", "SİSTEM", "GÜNCEL", "ADALET"],
    7: ["İSTATİK", "ÖĞRENCİ", "FAKÜLTE", "KAMPÜS", "BÖLÜMLÜ", "GELECEK", "AKADEMİ"]
}

# --- OYUN AKIŞI ---
if 'game_status' not in st.session_state:
    st.session_state.game_status = "login"

# Yan Panel: Lider Tablosu
with st.sidebar:
    st.header("🏆 Global Skorlar")
    df_scores = get_leaderboard()
    if not df_scores.empty:
        st.dataframe(df_scores.sort_values(by="Puan", ascending=False).head(10), hide_index=True)

st.title("✍️ Kelime Tahmin Oyunu")

if st.session_state.game_status == "login":
    name = st.text_input("İsminizi girin:", placeholder="ssxar")
    if st.button("Başla") and name:
        st.session_state.username = name
        st.session_state.game_status = "setup"
        st.rerun()

elif st.session_state.game_status == "setup":
    st.write(f"Hoş geldin **{st.session_state.username}**!")
    diff = st.radio("Zorluk:", [5, 6, 7], horizontal=True)
    if st.button("Kelimemi Belirle"):
        st.session_state.word_len = diff
        st.session_state.secret_word = random.choice(TURKISH_WORDS[diff]).upper()
        st.session_state.attempts = []
        st.session_state.game_status = "playing"
        st.rerun()

elif st.session_state.game_status == "playing":
    # 5 Haklık Oyun Alanı
    for i in range(5):
        cols = st.columns(st.session_state.word_len)
        if i < len(st.session_state.attempts):
            guess, feedback = st.session_state.attempts[i]
            for j in range(st.session_state.word_len):
                style = "correct-pos" if feedback[j] == "green" else ("wrong-pos" if feedback[j] == "orange" else "")
                cols[j].markdown(f"<div class='letter-slot {style}'>{guess[j]}</div>", unsafe_allow_html=True)
        else:
            for j in range(st.session_state.word_len):
                cols[j].markdown("<div class='letter-slot'> </div>", unsafe_allow_html=True)

    with st.form(key='guess_form', clear_on_submit=True):
        u_input = st.text_input("Tahmin ve Enter:").upper()
        if st.form_submit_button("Gönder"):
            if len(u_input) == st.session_state.word_len:
                sec = list(st.session_state.secret_word); gue = list(u_input); res = [""] * st.session_state.word_len
                for k in range(st.session_state.word_len):
                    if gue[k] == sec[k]: res[k] = "green"; sec[k] = None; gue[k] = "DONE"
                for k in range(st.session_state.word_len):
                    if gue[k] != "DONE" and gue[k] in sec: res[k] = "orange"; sec[sec.index(gue[k])] = None
                
                st.session_state.attempts.append((u_input, res))
                
                if u_input == st.session_state.secret_word:
                    puan = (6 - len(st.session_state.attempts)) * 20
                    save_score(st.session_state.username, puan, len(st.session_state.attempts))
                    st.session_state.game_status = "won"
                elif len(st.session_state.attempts) >= 5:
                    st.session_state.game_status = "lost"
                st.rerun()

if st.session_state.game_status == "won":
    st.balloons()
    st.success(f"Tebrikler! Kelime: {st.session_state.secret_word}")
    if st.button("Tekrar Oyna"): st.session_state.game_status = "setup"; st.rerun()
elif st.session_state.game_status == "lost":
    st.error(f"Maalesef! Doğru: {st.session_state.secret_word}")
    if st.button("Tekrar Dene"): st.session_state.game_status = "setup"; st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>made by ssxar</p>", unsafe_allow_html=True)