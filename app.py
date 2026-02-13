import streamlit as st
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Sayfa Ayarları
st.set_page_config(page_title="Ateşli Çocuklar Kelime Savaşları", page_icon="🔥", layout="centered")

# --- CSS: HELVETICA, MOBİL UYUM VE GÖRSEL TASARIM ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; }
    .word-row { display: flex; justify-content: center; margin-bottom: 6px; gap: 4px; }
    .letter-slot { 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        font-size: 20px; font-weight: bold; border: 2px solid #333; border-radius: 5px; 
        width: 38px; height: 38px; text-align: center; line-height: 38px; text-transform: uppercase;
    }
    .correct-pos { border-bottom: 5px solid #28a745 !important; background-color: #e6ffed; } 
    .wrong-pos { border-bottom: 5px solid #fd7e14 !important; background-color: #fff5e6; }
    .score-display { font-size: 32px; font-weight: bold; color: #ff4b4b; text-align: center; margin: 15px; }
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(worksheet="Sayfa1", ttl="0m")
    except:
        return pd.DataFrame(columns=["Email", "İsim", "Toplam_puan", "Oyun_sayisi"])

def update_db(email, name, points):
    df = get_data()
    df['Email'] = df['Email'].astype(str).str.strip()
    if email in df['Email'].values:
        idx = df[df['Email'] == email].index[0]
        df.at[idx, 'Toplam_puan'] = int(df.at[idx, 'Toplam_puan']) + points
        df.at[idx, 'Oyun_sayisi'] = int(df.at[idx, 'Oyun_sayisi']) + 1
    else:
        new_data = pd.DataFrame([{"Email": email, "İsim": name, "Toplam_puan": points, "Oyun_sayisi": 1}])
        df = pd.concat([df, new_data], ignore_index=True)
    conn.update(worksheet="Sayfa1", data=df)

# --- KELİME HAVUZU (Burayı 700 kelimeye kadar uzatabilirsin) ---
WORDS = {
    5: ["KALEM", "KİTAP", "DENİZ", "GÜNEŞ", "SINAV", "BAHAR", "CÜMLE", "DÜNYA", "EĞİTİM", "FİKİR", "HABER", "İNSAN", "MÜZİK", "OKUL", "RESİM", "ŞEHİR", "TARİH", "ZAMAN", "ARABA", "BEYAZ"],
    6: ["TÜRKÇE", "SÖZCÜK", "STATİK", "TASARIM", "MİMARİ", "SİSTEM", "GÜNCEL", "ADALET", "BİLGİN", "KÜLTÜR", "MANTIK", "ÖZGÜR", "TOPLUM", "VARLIK", "YARDIM", "BELLEK"],
    7: ["İSTATİK", "ÖĞRENCİ", "FAKÜLTE", "KAMPÜS", "BÖLÜMLÜ", "GELECEK", "AKADEMİ", "BAŞARI", "CESARET", "DEĞİŞİM", "FELSEFE", "YETENEK", "ZİHNİYET", "ANLAMLI", "BİLİMSEL"]
}

if 'game_status' not in st.session_state:
    st.session_state.game_status = "login"

# --- YAN PANEL ---
with st.sidebar:
    st.title("🏆 Liderler (Top 10)")
    leaderboard = get_data()
    if not leaderboard.empty:
        st.dataframe(leaderboard[["İsim", "Toplam_puan"]].sort_values(by="Toplam_puan", ascending=False).head(10), hide_index=True)
    
    st.markdown("---")
    st.subheader("📖 Oyun Kuralları")
    st.write("Hedef kelimeyi bulmak için **7 hakkın** var.")
    st.write("🟩 **Yeşil Çizgi:** Harf doğru yerde.")
    st.write("🟧 **Turuncu Çizgi:** Harf var ama yeri yanlış.")
    st.markdown("---")
    st.subheader("🎯 Puanlama Sistemi")
    st.write("1. Tahmin: 100p | 2. Tahmin: 80p")
    st.write("3. Tahmin: 60p | 4. Tahmin: 40p")
    st.write("5. Tahmin: 20p | 6. Tahmin: 15p")
    st.write("7. Tahmin: 10p")

st.title("🔥 Ateşli Çocuklar Kelime Savaşları")

# --- OYUN AKIŞI ---
if st.session_state.game_status == "login":
    st.info("Puanlarınızın kaydedilmesi için giriş yapın.")
    u_email = st.text_input("E-mail Adresiniz:").strip()
    u_name = st.text_input("Görünecek Adınız:").strip()
    if st.button("Savaşa Başla") and u_email and u_name:
        st.session_state.email = u_email
        st.session_state.username = u_name
        st.session_state.game_status = "setup"
        st.rerun()

elif st.session_state.game_status == "setup":
    st.subheader(f"Hoş geldin Savaşçı {st.session_state.username}!")
    choice = st.radio("Savaş Alanı (Harf Sayısı):", [5, 6, 7], horizontal=True, help="Harf sayısı arttıkça ödül kazanmak zorlaşır!")
    if st.button("Kelimeyi Getir"):
        st.session_state.word_len = choice
        st.session_state.secret = random.choice(WORDS[choice]).upper()
        st.session_state.tries = []
        st.session_state.game_status = "playing"
        st.rerun()

elif st.session_state.game_status == "playing":
    # Tahmin Alanı (Mobil Uyumlu)
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
        guess_in = st.text_input("Tahmininizi yazın ve Enter'a basın:").replace('i', 'İ').replace('ı', 'I').upper()
        if st.form_submit_button("Saldır!"):
            if len(guess_in) == st.session_state.word_len:
                sol = list(st.session_state.secret); gue = list(guess_in); res = [""] * st.session_state.word_len
                # Önce yeşiller
                for k in range(st.session_state.word_len):
                    if gue[k] == sol[k]: res[k] = "correct-pos"; sol[k] = None; gue[k] = "DONE"
                # Sonra turuncular
                for k in range(st.session_state.word_len):
                    if gue[k] != "DONE" and gue[k] in sol: res[k] = "wrong-pos"; sol[sol.index(gue[k])] = None
                
                st.session_state.tries.append((guess_in, res))
                
                if guess_in == st.session_state.secret:
                    pts = {1: 100, 2: 80, 3: 60, 4: 40, 5: 20, 6: 15, 7: 10}.get(len(st.session_state.tries), 0)
                    update_db(st.session_state.email, st.session_state.username, pts)
                    st.session_state.last_p = pts
                    st.session_state.game_status = "won"
                elif len(st.session_state.tries) >= 7:
                    st.session_state.game_status = "lost"
                st.rerun()

if st.session_state.game_status == "won":
    st.balloons()
    st.markdown(f"<div class='score-display'>🚩 +{st.session_state.last_p} PUAN KAZANILDI! 🚩</div>", unsafe_allow_html=True)
    st.success(f"Zafer senin! Doğru kelime: {st.session_state.secret}")
    if st.button("Yeni Savaş"): st.session_state.game_status = "setup"; st.rerun()
elif st.session_state.game_status == "lost":
    st.error(f"Savaşı kaybettin! Doğru kelime: {st.session_state.secret}")
    if st.button("Tekrar Dene"): st.session_state.game_status = "setup"; st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>made by ssxar</p>", unsafe_allow_html=True)
