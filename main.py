#main.py
import io
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware   # 1. BU SATIRI EKLE

app = FastAPI(title="Hisse Analiz API", description="Hisse senedi analizleri için API", version="1.0.0")
# 2. BU BLOĞU EKLE (app satırının hemen altına)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def veri_cek(hisse: str, baslangic: str, bitis: str):
    veri = yf.Ticker(hisse).history(start=baslangic, end=bitis)
    if veri.empty:
        raise HTTPException(status_code=404, detail="Veri bulunamadı.")
    return veri

def grafik_gonder():
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")

@app.get("/")
def ana_sayfa():
    return {"message": "Hisse Analiz API'ye hoş geldiniz. /grafik1 veya /grafik2 endpointlerini kullanabilirsiniz."}

@app.get("/grafik/zirve-dip/{hisse}")
def grafik1(hisse: str, baslangic: str = "2021-01-01", bitis: str = "2026-06-30"):
    veri = veri_cek(hisse, baslangic, bitis)
    en_yuksek_tarih = veri["Close"].idxmax()
    en_yuksek_fiyat = veri["Close"].max()
    en_dusuk_tarih = veri["Close"].idxmin()
    en_dusuk_fiyat = veri["Close"].min()

    plt.figure(figsize=(10, 5))
    plt.plot(veri.index, veri["Close"], color="blue")
    plt.scatter(en_yuksek_tarih, en_yuksek_fiyat, color="green", s=100, zorder=5)
    plt.scatter(en_dusuk_tarih, en_dusuk_fiyat, color="red", s=100, zorder=5)
    plt.annotate(f"En Yüksek: {en_yuksek_fiyat:.2f}", (en_yuksek_tarih, en_yuksek_fiyat))
    plt.annotate(f"En Düşük: {en_dusuk_fiyat:.2f}", (en_dusuk_tarih, en_dusuk_fiyat))
    plt.title(f"{hisse} - En Yüksek/Düşük Noktalar")
    plt.xlabel("Tarih");  plt.ylabel("Fiyat (TL)");  plt.grid(True)
    return grafik_gonder()

@app.get("/grafik/aylik/{hisse}")
def grafik2(hisse: str, baslangic: str = "2021-01-01", bitis: str = "2026-06-30"):
    veri = veri_cek(hisse, baslangic, bitis)
    aylik_degisim = (veri["Close"].resample("ME").last().pct_change() * 100).dropna()
    renkler = ["green" if x >= 0 else "red" for x in aylik_degisim]

    plt.figure(figsize=(12, 5))
    plt.bar(aylik_degisim.index, aylik_degisim, color=renkler, width=20)
    plt.title(f"{hisse} - Aylık Yüzde Değişim")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.grid(True, axis="y")
    return grafik_gonder()


@app.get("/grafik/haftalik/{hisse}")
def grafik4(hisse: str, baslangic: str = "2021-01-01", bitis: str = "2026-06-30"):
    veri = veri_cek(hisse, baslangic, bitis)
    haftalik_degisim = (veri["Close"].resample("W").last().pct_change() * 100).dropna()
    renkler = ["green" if x >= 0 else "red" for x in haftalik_degisim]

    plt.figure(figsize=(12, 5))
    plt.bar(haftalik_degisim.index, haftalik_degisim, color=renkler, width=5)
    plt.title(f"{hisse} - Haftalık Yüzde Değişim")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.grid(True, axis="y")
    return grafik_gonder()

@app.get("/grafik/kumulatif/{hisse}")
def  grafik3(hisse: str, baslangic: str= "2021-01-01", bitis: str = "2026-06-30"):
    veri = veri_cek(hisse, baslangic, bitis)
    ilk_fiyat = veri["Close"].iloc[0]
    kumulatif_degisim = ((veri["Close"] - ilk_fiyat) / ilkfiyat) * 100
    renk = "green" if kumulatif.iloc[-1] >= 0 else "red"

    plt.figure(figsize=(10, 5))
    plt.plot(veri.index, kumulatif_degisim, color=renk)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title(f"{hisse} - Kümülatif Yüzde Değişim")
    plt.grid(True)
    return grafik_gonder()

@app.get("/ozet/{hisse}")
def ozet(hisse: str, baslangic: str = "2021-01-01", bitis: str = "2026-06-30"):
    veri = veri_cek(hisse, baslangic, bitis)
    aylik_degisim = (veri["Close"].resample("ME").last().pct_change() * 100).dropna()
    ilk, son = veri["Close"].iloc[0], veri["Close"].iloc[-1]
    return {
        "hisse": hisse,
        "en_yuksek": {"fiyat": round(veri["Close"].max(), 2), "tarih": str(veri["Close"].idxmax().date())},
        "en_dusuk": {"fiyat": round(veri["Close"].min(), 2), "tarih": str(veri["Close"].idxmin().date())},
        "kumulatif_degisim_yuzde": round((son - ilk) / ilk * 100, 2),
        "aylik_degisimler": {str(t.date()): round(d, 2) for t, d in aylik_degisim.items()},
    }

@app.get("/haftalik-ozet/{hisse}")
def haftalik_ozet(hisse: str, baslangic: str = "2021-01-01", bitis: str = "2026-06-30"):
    veri = veri_cek(hisse, baslangic, bitis)
    haftalik_degisim = (veri["Close"].resample("W").last().pct_change() * 100).dropna()
    return {
        "hisse": hisse,
        "haftalik_degisimler": {str(t.date()): round(d, 2) for t, d in haftalik_degisim.items()},
    }
