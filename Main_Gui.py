import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import subprocess
import os
import sys

def kaynak_yolu(dosya_adi):
    """PyInstaller ile uyumlu dosya yolu üretir"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, dosya_adi)
    return os.path.join(os.path.abspath("."), dosya_adi)

class AnaUygulama:
    def __init__(self, root):
        self.root = root
        self.root.title("ReachSuite")
        try:
            self.root.iconbitmap(kaynak_yolu("ReachSuiteIcon.ico"))
        except:
            print("Icon yüklenemedi.")

        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        # Üstte PNG başlık/logoyu göster
        try:
            logo_img = Image.open(kaynak_yolu("assets/banner.png")).resize((500, 100), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            banner_label = tk.Label(root, image=logo_photo, bg="#f0f0f0")
            banner_label.image = logo_photo
            banner_label.pack(pady=(60, 40))
        except:
            print("Banner yüklenemedi.")

        # Uygulama seçim alanı
        self.app_frame = tk.Frame(root, bg="#f0f0f0")
        self.app_frame.pack(pady=(0, 60))

        # Uygulamalar
        self.uygulamalar = [
            {
                "ad": "Google Maps Veri Kazıma",
                "logo": "assets/maps_logo.png",
                "button": "assets/start_targetmap.png",
                "script": "google_maps_scraper.py"
            },
            {
                "ad": "Web Sitesi Email Kazıma",
                "logo": "assets/email_logo.png",
                "button": "assets/start_mailscout.png",
                "script": "email_scraper.py"
            },
            {
                "ad": "Toplu Email Gönderme",
                "logo": "assets/email_send_logo.png",
                "button": "assets/start_mailpilot.png",
                "script": "mail_sender.py"
            }
        ]

        self.logo_list = []
        self.button_list = []

        for i, uygulama in enumerate(self.uygulamalar):
            self.uygulama_butonu_olustur(uygulama, i)

    def uygulama_butonu_olustur(self, uygulama, index):
        frame = tk.Frame(self.app_frame, bg="#f0f0f0")
        frame.grid(row=0, column=index, padx=20, pady=10)

        # Logo
        try:
            img = Image.open(kaynak_yolu(uygulama["logo"])).resize((150, 140), Image.LANCZOS)
            logo = ImageTk.PhotoImage(img)
            self.logo_list.append(logo)
            tk.Label(frame, image=logo, bg="#f0f0f0").pack(pady=10)
        except:
            tk.Label(frame, text="LOGO", bg="#f0f0f0", width=10, height=5).pack(pady=10)

        # PNG buton
        try:
            buton_img = Image.open(kaynak_yolu(uygulama["button"])).resize((100, 40), Image.LANCZOS)
            buton_photo = ImageTk.PhotoImage(buton_img)
            self.button_list.append(buton_photo)
            btn = tk.Button(frame, image=buton_photo, bg="#f0f0f0", bd=0,
                            command=lambda u=uygulama: self.uygulama_baslat(u))
            btn.pack(pady=10)
        except:
            tk.Button(frame, text="Başlat", command=lambda u=uygulama: self.uygulama_baslat(u),
                      bg="#4CAF50", fg="white", width=12).pack(pady=10)

    def uygulama_baslat(self, uygulama):
        try:
            script_yolu = kaynak_yolu(uygulama["script"])
            if not os.path.exists(script_yolu):
                raise FileNotFoundError(f"{uygulama['script']} bulunamadı!")
            subprocess.Popen(f'start cmd /k python "{script_yolu}"', shell=True)
        except Exception as e:
            messagebox.showerror("Hata", f"{uygulama['ad']} başlatılamadı:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnaUygulama(root)
    root.mainloop()
