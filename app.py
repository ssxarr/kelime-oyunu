import streamlit as st
import random
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Sayfa Ayarları (En Üstte Olmalı)
st.set_page_config(page_title="Ateşli Çocuklar Kelime Savaşları", page_icon="🔥", layout="centered")

# --- CSS: TASARIM VE MOBİL UYUM ---
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important; }
    .word-row { display: flex; justify-content: center; margin-bottom: 6px; gap: 4px; }
    .letter-slot { 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        font-size: 18px; font-weight: bold; border: 2px solid #333; border-radius: 5px; 
        width: 38px; height: 38px; text-align: center; line-height: 38px; text-transform: uppercase;
    }
    .correct-pos { border-bottom: 5px solid #28a745 !important; background-color: #e6ffed; } 
    .wrong-pos { border-bottom: 5px solid #fd7e14 !important; background-color: #fff5e6; }
</style>
""", unsafe_allow_html=True)

# 2. Bağlantıyı Kur
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # ttl="0" ile her seferinde sıfırdan okumasını sağlıyoruz
        data = conn.read(worksheet="Sayfa1", ttl="0")
        if data is None or data.empty:
            return pd.DataFrame(columns=["Email", "Isim", "Toplam_Puan", "Oyun_Sayisi"])
        return data
    except Exception:
        # Hata durumunda boş tablo döndür ki oyun çökmesin
        return pd.DataFrame(columns=["Email", "Isim", "Toplam_Puan", "Oyun_Sayisi"])
def update_db(email, name, points):
    try:
        df = get_data()
        # Email sütununu kontrol et ve temizle
        df['Email'] = df['Email'].astype(str).str.strip()
        
        if email in df['Email'].values:
            idx = df[df['Email'] == email].index[0]
            # Değerleri sayıya çevirip üzerine ekle
            df.at[idx, 'Toplam_Puan'] = int(df.at[idx, 'Toplam_Puan'] or 0) + points
            df.at[idx, 'Oyun_Sayisi'] = int(df.at[idx, 'Oyun_Sayisi'] or 0) + 1
        else:
            new_row = pd.DataFrame([{"Email": email, "Isim": name, "Toplam_Puan": points, "Oyun_Sayisi": 1}])
            df = pd.concat([df, new_row], ignore_index=True)
        
        # TABLOYU GÜNCELLE
        conn.update(worksheet="Sayfa1", data=df)
        st.toast("Skor başarıyla kaydedildi! 🏆")
    except Exception as e:
        st.sidebar.error("Kayıt başarısız! Lütfen hizmet hesabının 'Düzenleyici' yetkisini kontrol et.")

# 3. Oyun Verileri ve Havuzu
WORDS = {
    5: ["KALEM", "KİTAP", "DENİZ", "GÜNEŞ", "SINAV", "BAHAR", "CÜMLE", "DÜNYA", "EĞİTİM", "FİKİR"],
    6: ["TÜRKÇE", "SÖZCÜK", "STATİK", "TASARIM", "MİMARİ", "SİSTEM", "GÜNCEL", "ADALET"],
    7: ["İSTATİK", "ÖĞRENCİ", "FAKÜLTE", "KAMPÜS", "BÖLÜMLÜ", "GELECEK", "AKADEMİ"]
}

if 'game_status' not in st.session_state:
    st.session_state.game_status = "login"

# --- YAN PANEL (LİDER TABLOSU) ---
with st.sidebar:
    st.title("🏆 Lider Savaşçılar")
    lb = get_data()
    if not lb.empty:
        st.dataframe(lb[["Isim", "Toplam_Puan"]].sort_values(by="Toplam_Puan", ascending=False).head(10), hide_index=True)
    st.markdown("---")
    st.subheader("🎯 Ödül Puanları")
    st.write("1. 100p | 2. 80p | 3. 60p | 4. 40p | 5. 20p | 6. 15p | 7. 10p")

st.title("🔥 Ateşli Çocuklar Kelime Savaşları")

# 4. Oyun Akışı
if st.session_state.game_status == "login":
    u_email = st.text_input("E-mail (Puan Takibi İçin):").strip()
    u_name = st.text_input("Görünecek Adınız:").strip()
    if st.button("Savaşa Başla") and u_email and u_name:
        st.session_state.email = u_email
        st.session_state.username = u_name
        st.session_state.game_status = "setup"
        st.rerun()

elif st.session_state.game_status == "setup":
    st.subheader(f"Savaşçı: {st.session_state.username}")
    choice = st.radio("Harf Sayısı Seçin:", [5, 6, 7], horizontal=True)
    if st.button("Kelimeyi Getir"):
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
            for j in range(st.session_state.word_len): row_html += "<div class='letter-slot'> </div>"
        row_html += "</div>"
        st.markdown(row_html, unsafe_allow_html=True)

    with st.form(key='guess_form', clear_on_submit=True):
        guess_in = st.text_input("Tahmin:").replace('i', 'İ').replace('ı', 'I').upper()
        if st.form_submit_button("Saldır!"):
            if len(guess_in) == st.session_state.word_len:
                sol = list(st.session_state.secret); gue = list(guess_in); res = [""] * st.session_state.word_len
                for k in range(st.session_state.word_len):
                    if gue[k] == sol[k]: res[k] = "correct-pos"; sol[k] = None; gue[k] = "X"
                for k in range(st.session_state.word_len):
                    if gue[k] != "X" and gue[k] in sol: res[k] = "wrong-pos"; sol[sol.index(gue[k])] = None
                
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
    st.balloons(); st.success(f"Zafer senin! Kelime: {st.session_state.secret}")
    if st.button("Yeni Savaş"): st.session_state.game_status = "setup"; st.rerun()
elif st.session_state.game_status == "lost":
    st.error(f"Maalesef elendin! Doğru kelime: {st.session_state.secret}")
    if st.button("Tekrar Dene"): st.session_state.game_status = "setup"; st.rerun()

st.markdown("---")
st.markdown("<p style='text-align: center; color: grey;'>made by ssxar</p>", unsafe_allow_html=True)
