import streamlit as st
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Sayfa Ayarları
st.set_page_config(page_title="Ateşli Çocuklar Kelime Savaşları", page_icon="🔥", layout="centered")

# --- CSS: HELVETICA VE MOBİL UYUM ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; }
    .word-row { display: flex; justify-content: center; margin-bottom: 6px; gap: 4px; }
    .letter-slot { 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        font-size: 18px; font-weight: bold; border: 2px solid #333; border-radius: 5px; 
        width: 35px; height: 35px; text-align: center; line-height: 35px; text-transform: uppercase;
    }
    .correct-pos { border-bottom: 5px solid #28a745 !important; background-color: #e6ffed; } 
    .wrong-pos { border-bottom: 5px solid #fd7e14 !important; background-color: #fff5e6; }
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(worksheet="Sayfa1", ttl="0m")
    except:
        return pd.DataFrame(columns=["Email", "Isim", "Toplam_Puan", "Oyun_Sayisi"])

def update_db(email, name, points):
    try:
        df = get_data()
        df['Email'] = df['Email'].astype(str).str.strip()
        if email in df['Email'].values:
            idx = df[df['Email'] == email].index[0]
            df.at[idx, 'Toplam_Puan'] = int(df.at[idx, 'Toplam_Puan']) + points
            df.at[idx, 'Oyun_Sayisi'] = int(df.at[idx, 'Oyun_Sayisi']) + 1
        else:
            new_data = pd.DataFrame([{"Email": email, "Isim": name, "Toplam_Puan": points, "Oyun_Sayisi": 1}])
            df = pd.concat([df, new_data], ignore_index=True)
        
        # VERİ YAZMA İŞLEMİ
        conn.update(worksheet="Sayfa1", data=df)
        st.toast("Skor başarıyla güncellendi! 🏆")
    except Exception as e:
        st.sidebar.error("Veri tabanına yazılamadı. Yetki sorunu olabilir.")

# --- YAN PANEL (Sidebar - Hata alsa bile görünmesi için en üstte) ---
with st.sidebar:
    st.title("🏆 Lider Savaşçılar")
    leaderboard = get_data()
    if not leaderboard.empty:
        st.dataframe(leaderboard[["Isim", "Toplam_Puan"]].sort_values(by="Toplam_Puan", ascending=False).head(10), hide_index=True)
    
    st.markdown("---")
    st.subheader("🎯 Ödül Puanları")
    st.write("1. Tahmin: 100p | 2. Tahmin: 80p")
    st.write("3. Tahmin: 60p | 4. Tahmin: 40p")
    st.write("5. Tahmin: 20p | 6. Tahmin: 15p | 7. Tahmin: 10p")

# --- KELİME HAVUZU ---
WORDS = {
    5: ["KALEM", "KİTAP", "DENİZ", "GÜNEŞ", "SINAV", "BAHAR", "CÜMLE", "DÜNYA", "EĞİTİM", "FİKİR"],
    6: ["TÜRKÇE", "SÖZCÜK", "STATİK", "TASARIM", "MİMARİ", "SİSTEM", "GÜNCEL", "ADALET"],
    7: ["İSTATİK", "ÖĞRENCİ", "FAKÜLTE", "KAMPÜS", "BÖLÜMLÜ", "GELECEK", "AKADEMİ"]
}

if 'game_status' not in st.session_state:
    st.session_state.game_status = "login"

st.title("🔥 Ateşli Çocuklar Kelime Savaşları")

# Giriş ve Oyun Mantığı
if st.session_state.game_status == "login":
    st.info("Puanlarınızın kaydedilmesi için giriş yapın.")
    u_email = st.text_input("E-mail:").strip()
    u_name = st.text_input("İsim:").strip()
    if st.button("Savaşa Başla") and u_email and u_name:
        st.session_state.email = u_email
        st.session_state.username = u_name
        st.session_state.game_status = "setup"
        st.rerun()

elif st.session_state.game_status == "setup":
    choice = st.radio("Harf Sayısı Seçin:", [5, 6, 7], horizontal=True)
    if st.button("Saldır"):
        st.session_state.word_len = choice
        st.session_state.secret = random.choice(WORDS[choice]).upper()
        st.session_state.tries = []
        st.session_state.game_status = "playing"
        st.rerun()

elif st.session_state.game_status == "playing":
    for i in range(7):
        row_html = "<div class='word-row'>"
        if i < len(st.session_state.tries):
            guess, colors = st.session_state.tries[i]
            for j in range(st.session_state.word_len):
                row_html += f"<div class='letter-slot {colors[j]}'>{guess[j]}</div>"
        else:
            for j in range(st.session_state.word_len):
                row_html += "<div class='letter-slot'> </div>"
        row_html += "</div>"
        st.markdown(row_html, unsafe_allow_html=True)

    with st.form(key='guess_form', clear_on_submit=True):
        guess_in = st.text_input("Tahmin:").replace('i', 'İ').replace('ı', 'I').upper()
        if st.form_submit_button("Tahmin Et"):
            if len(guess_in) == st.session_state.word_len:
                sol = list(st.session_state.secret); gue = list(guess_in); res = [""] * st.session_state.word_len
                for k in range(st.session_state.word_len):
                    if gue[k] == sol[k]: res[k] = "correct-pos"; sol[k] = None; gue[k] = "DONE"
                for k in range(st.session_state.word_len):
                    if gue[k] != "DONE" and gue[k] in sol: res[k] = "wrong-pos"; sol[sol.index(gue[k])] = None
                
                st.session_state.tries.append((guess_in, res))
                
                if guess_in == st.session_state.secret:
                    pts = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20, 6: 15, 7: 10}.get(len(st.session_state.tries), 0)
                    update_db(st.session_state.email, st.session_state.username, pts)
                    st.session_state.game_status = "won"
                elif len(st.session_state.tries) >= 7:
                    update_db(st.session_state.email, st.session_state.username, 0)
                    st.session_state.game_status = "lost"
                st.rerun()

if st.session_state.game_status == "won":
    st.balloons(); st.success(f"Zafer! Kelime: {st.session_state.secret}")
    if st.button("Yeni Oyun"): st.session_state.game_status = "setup"; st.rerun()
elif st.session_state.game_status == "lost":
    st.error(f"Maalesef! Doğru: {st.session_state.secret}")
    if st.button("Tekrar Dene"): st.session_state.game_status = "setup"; st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>made by ssxar</p>", unsafe_allow_html=True)
