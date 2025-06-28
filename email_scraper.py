import tkinter as tk
from tkinter import messagebox, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re
import pandas as pd
import threading
import os
from PIL import Image, ImageTk
from urllib.parse import urlparse, urljoin
import hashlib
import sys

import sys, os

def resource_path(relative_path):
    try:
        return os.path.join(sys._MEIPASS, relative_path)
    except Exception:
        return os.path.join(os.path.abspath("."), relative_path)

# === Dosya yolları ===
IMG_PATH = resource_path("fatih.png")
BUTTON_IMG_PATH = resource_path("mailleri_tespit_et.png")
ICON_PATH = resource_path("fk_icon.ico")
MAIL_LOGO_PATH = resource_path("mail_logo.png")

email_regex = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# Hedef kelimeler (çok dilli)
target_keywords = [
    # Türkçe
    "iletişim", "bize ulaşın", "iletisim", "kontakt", "bizimle temasa geç", "bize yazın",

    # İngilizce
    "contact", "get in touch", "contact us", "reach us", "write to us",

    # Almanca
    "kontakt", "kontaktieren", "uns erreichen", "schreiben Sie uns", "uns schreiben",

    # İspanyolca
    "contacto", "ponerse en contacto", "escribir a nosotros", "contactarnos",

    # İtalyanca
    "contatto", "scrivici", "mettersi in contatto", "contattaci",

    # Rusça
    "контакт", "связаться с нами", "напишите нам", "связаться с нами",

    # Portekizce
    "contacto", "entrar em contato", "escrever para nós", "nos contatar",

    # Fransızca
    "nous contacter", "prendre contact", "écrire à nous", "entrer en contact",

    # Felemenkçe (Hollandaca)
    "contacteer", "schrijf ons", "contact met ons opnemen", "ons bereiken",

    # İbranice
    "מצורף", "צרו קשר", "כתבו אלינו",

    # Çekçe
    "kontaktujte nás", "napíšte nám", "spojte se s námi",

    # Ukraynaca
    "контакт", "свяжитесь с нами", "напишите нам",

    # Sırpça
    "kontakt", "kontaktirajte nas", "pišite nam", "obratite se", "kontaktirajte nas",

    # Hırvatça
    "kontakt", "kontaktirajte nas", "pišite nam", "obratite nam se",

    # Bulgarca
    "контакт", "свържете се с нас", "напишете ни", "обратна връзка",

    # Arapça
    "اتصل بنا", "تواصل معنا", "راسلنا", "اتصل بنا", "اكتب لنا",

    # Farsça (Persce)
    "تماس با ما", "با ما ارتباط برقرار کنید", "با ما بنویسید",

    # Yunanca
    "επικοινωνία", "επικοινωνήστε μαζί μας", "γράψτε μας", "επικοινωνήστε μαζί μας",

    # Macarca
    "kapcsolat", "lépjen kapcsolatba velünk", "írjon nekünk", "elérhetőség",

    # Polonyaca
    "kontakt", "skontaktuj się z nami", "napisz do nas", "z nami kontakt",

    # Arnavutça
    "kontakt", "kontaktoni me ne", "na shkruani", "kontaktoni me ne",

    # Romence
    "contactați-ne", "scrieți-ne", "contactați-ne", "scrieți la noi",

    # İsveççe
    "kontakt", "kontakta oss", "skriv till oss", "kom i kontakt",

    # Danca
    "kontakt", "kontakt os", "skriv til os", "kom i kontakt med os",

    # Norveççe
    "kontakt", "kontakt oss", "skriv til oss", "kom i kontakt med oss",

    # Finlandiya
    "yhteydenotto", "ota yhteyttä", "kirjoita meille", "yhteystiedot",

    # Arapça (Mısır)
    "اتصل بنا", "تواصل معنا", "راسلنا", "اتصل بنا", "اكتب لنا",

    # Tunus Arapçası
    "اتصل بنا", "تواصل معنا", "راسلنا", "اتصل بنا",

    # Endonezce
    "kontak", "hubungi kami", "tulis kepada kami", "berhubung dengan kami",

    # Malayca
    "hubungi kami", "menghubungi kami", "tulis kepada kami", "berhubung dengan kami",

    # Somali
    "nala soo xiriir", "nagu soo qor", "nagula xiriir", "nala soo xiriir",

    # Swahili
    "wasiliana nasi", "andika kwetu", "tuandikie", "fikia nasi",

    # Makedonca
    "контакт", "контактирајте не", "пишете ни", "Контакт", "стапете во контакт",

    # Boşnakça
    "kontakt", "kontaktirajte nas", "kontakti", "pišite nam", "obratite nam se"
]

def is_valid_url(url):
    parsed = urlparse(url)
    return parsed.scheme in ["http", "https"] and bool(parsed.netloc)

def normalize_url(url, base_url):
    if not url.startswith("http"):
        url = urljoin(base_url, url)
    parsed = urlparse(url)
    return parsed.scheme + "://" + parsed.netloc + parsed.path.rstrip('/')

def generate_content_hash(content):
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def close_popups():
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.XPATH, "//*[contains(text(), 'Kabul') or contains(text(), 'Tamam') or contains(text(), 'OK') or contains(text(), 'I accept')]")
        )).click()
        time.sleep(1)
    except Exception:
        pass

def extract_emails(urls):
    all_data = []
    visited_contact_hashes = set()
    total_urls = len(urls)
    progress_bar["maximum"] = total_urls
    progress_bar["value"] = 0
    update_progress_text(0, total_urls)

    for index, url in enumerate(urls, start=1):
        try:
            driver.get(url)
            close_popups()
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, "html.parser")
            page_data = {"URL": url, "Emails": set()}

            for link in soup.find_all("a", href=True):
                href = link["href"]
                if "mailto:" in href:
                    page_data["Emails"].add(href.split("mailto:")[1].split("?")[0])
            page_data["Emails"].update(re.findall(email_regex, soup.text))

            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True).lower()
                href = link["href"]
                if any(k in text for k in target_keywords) or 'contact' in href.lower():
                    normalized = normalize_url(href, url)
                    hash_ = generate_content_hash(soup.text)
                    if normalized not in visited_contact_hashes and hash_ not in visited_contact_hashes:
                        visited_contact_hashes.add(hash_)
                        try:
                            driver.get(normalized)
                            close_popups()
                            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                            time.sleep(2)
                            contact_soup = BeautifulSoup(driver.page_source, "html.parser")
                            for l in contact_soup.find_all("a", href=True):
                                if "mailto:" in l["href"]:
                                    page_data["Emails"].add(l["href"].split("mailto:")[1].split("?")[0])
                            page_data["Emails"].update(re.findall(email_regex, contact_soup.text))
                        except Exception:
                            pass

            all_data.append(page_data)
        except Exception as e:
            print(f"Hata oluştu: {url} atlandı: {e}")
        progress_bar["value"] = index
        update_progress_text(index, total_urls)

    driver.quit()
    final_data = []
    for page in all_data:
        url = page["URL"]
        for i, mail in enumerate(page["Emails"]):
            final_data.append([url if i == 0 else "", mail])

    pd.DataFrame(final_data, columns=["URL", "Email"]).to_excel("web_emails.xlsx", index=False)
    pd.DataFrame(final_data, columns=["URL", "Email"]).to_csv("web_emails.csv", index=False)
    messagebox.showinfo("Bitti", "E-postalar kaydedildi.")

def update_progress_text(current, total):
    progress_text.config(text=f"İlerleme: {current}/{total}")
    root.update_idletasks()

def load_profile_image():
    try:
        img = Image.open(IMG_PATH).resize((250, 250))
        img_tk = ImageTk.PhotoImage(img)
        profile_image_label.config(image=img_tk)
        profile_image_label.image = img_tk
    except Exception as e:
        print(f"Fotoğraf hatası: {e}")

def get_urls():
    urls_input = text_box.get("1.0", tk.END).strip()
    if not urls_input:
        messagebox.showwarning("Uyarı", "Lütfen en az bir URL girin!")
        return

    raw_urls = [url.strip() for url in urls_input.splitlines() if url.strip()]
    normalized = []
    for url in raw_urls:
        if not url.startswith("http"):
            url = "http://" + url
        if is_valid_url(url):
            normalized.append(url)
        else:
            print("Geçersiz URL:", url)

    if not normalized:
        messagebox.showerror("Hata", "Geçerli URL yok.")
        return

    threading.Thread(target=extract_emails, args=(normalized,)).start()

def show_password_screen():
    pw = tk.Tk()
    pw.title("Giriş")
    pw.geometry("300x150")
    pw.configure(bg="#f4f4f4")
    tk.Label(pw, text="Şifre:", bg="#f4f4f4", font=("Arial", 12)).pack(pady=10)
    entry = tk.Entry(pw, show="*", font=("Arial", 12))
    entry.pack()

    def check():
        if entry.get() == "1234":
            pw.destroy()
            launch_main_app()
        else:
            messagebox.showerror("Hatalı", "Yanlış şifre!")

    tk.Button(pw, text="Giriş", command=check, bg="#dbeafe", font=("Arial", 12)).pack(pady=10)
    pw.mainloop()

def launch_main_app():
    global root, text_box, progress_bar, progress_text, profile_image_label, button_photo

    root = tk.Tk()
    root.title("MailScout")
    root.geometry("1000x700")
    root.configure(bg="#f4f4f4")

    try:
        root.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"ICO yükleme hatası: {e}")

    try:
        logo_img = Image.open(MAIL_LOGO_PATH).resize((300, 80))
        logo_tk = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(root, image=logo_tk, bg="#f4f4f4")
        logo_label.image = logo_tk
        logo_label.pack(pady=20)
    except Exception as e:
        print("Logo PNG hatası:", e)
        tk.Label(root, text="MailScout", font=("Arial", 20), bg="#f4f4f4").pack(pady=20)

    tk.Label(root, text="Web site URL’lerini girin (bir satıra bir tane)", bg="#f4f4f4").pack()
    text_box = tk.Text(root, height=20, width=60)
    text_box.pack(pady=10)

    try:
        btn_img = Image.open(BUTTON_IMG_PATH).resize((200, 60))
        button_photo = ImageTk.PhotoImage(btn_img)
        tk.Button(root, image=button_photo, command=get_urls, bg="#f4f4f4",
                  borderwidth=0, activebackground="#f4f4f4", cursor="hand2").pack(pady=10)
    except Exception as e:
        print("Buton PNG hatası:", e)
        tk.Button(root, text="Mailleri Tespit Et", command=get_urls).pack(pady=10)

    profile_frame = tk.Frame(root, bg="#f4f4f4")
    profile_frame.place(relx=1.0, rely=0.0, anchor="ne", x=0, y=30)
    profile_image_label = tk.Label(profile_frame, bg="#f4f4f4")
    profile_image_label.pack()
    load_profile_image()

    progress_text = tk.Label(root, text="İlerleme: 0/0", font=("Arial", 12), bg="#f4f4f4")
    progress_text.pack(pady=10)
    progress_bar = ttk.Progressbar(root, length=300, mode="determinate")
    progress_bar.pack(pady=5)

    root.mainloop()

# === Başlat ===
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(10)

show_password_screen()
