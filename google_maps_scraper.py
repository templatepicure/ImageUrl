import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import threading
import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller geçici klasörü
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def start_scraping():
    search_query = search_entry.get()
    if not search_query:
        messagebox.showwarning("Uyarı", "Lütfen bir arama kelimesi girin!")
        return
    threading.Thread(target=scrape_google_maps, args=(search_query,), daemon=True).start()

def update_progress_text(current, total):
    progress_label.config(text=f"İlerleme: {current}/{total}")
    progress_bar["value"] = current
    progress_bar["maximum"] = total
    root.update_idletasks()

def scrape_google_maps(search_query):
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = uc.Chrome(options=options)
    driver.get(f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}")

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]'))
        )
    except:
        messagebox.showerror("Hata", "Arama sonuçları yüklenemedi.")
        driver.quit()
        return

    business_data = []
    scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')

    last_count = 0
    scroll_attempts = 0
    while True:
        driver.execute_script("arguments[0].scrollTop += 1000;", scrollable_div)
        time.sleep(3)

        listings = driver.find_elements(By.XPATH, '//a[contains(@href, "https://www.google.com/maps/place")]')
        current_count = len(listings)

        if current_count == last_count:
            scroll_attempts += 1
            if scroll_attempts >= 5:
                break
        else:
            scroll_attempts = 0
        last_count = current_count

    business_links = [listing.get_attribute("href") for listing in listings if listing.get_attribute("href")]
    total_links = len(business_links)
    messagebox.showinfo("Bilgi", f"Toplam {total_links} işletme bulundu.")

    for index, link in enumerate(business_links):
        try:
            driver.get(link)
            time.sleep(5)

            name = driver.find_element(By.XPATH, '//h1').text
            address = driver.find_element(By.XPATH, '//button[@data-item-id="address"]').text if driver.find_elements(
                By.XPATH, '//button[@data-item-id="address"]') else "N/A"
            phone = driver.find_element(By.XPATH,
                                        '//button[contains(@data-item-id, "phone")]').text if driver.find_elements(
                By.XPATH, '//button[contains(@data-item-id, "phone")]') else "N/A"
            website = driver.find_element(By.XPATH, '//a[@data-item-id="authority"]').get_attribute(
                "href") if driver.find_elements(By.XPATH, '//a[@data-item-id="authority"]') else "N/A"
            reviews = driver.find_element(By.XPATH, '//span[@role="img"]').get_attribute(
                "aria-label") if driver.find_elements(By.XPATH, '//span[@role="img"]') else "N/A"

            business_data.append([name, address, phone, website, reviews])
            update_progress_text(index + 1, total_links)
        except:
            continue

    driver.quit()
    df = pd.DataFrame(business_data, columns=["İsim", "Adres", "Telefon", "Web Sitesi", "Yorumlar"])
    df.to_excel("google_maps_data.xlsx", index=False)
    df.to_csv("google_maps_data.csv", index=False)
    messagebox.showinfo("Tamamlandı", "Veriler başarıyla kaydedildi!")

def launch_main_app():
    global root, search_entry, progress_label, progress_bar

    root = tk.Tk()
    root.title("Potansiyel Bulucu")
    root.geometry("500x550")
    root.resizable(False, False)
    root.configure(bg="#f4f4f4")

    icon_path = resource_path("logo.ico")
    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    else:
        print("logo.ico dosyası bulunamadı!")

    main_frame = tk.Frame(root, bg="#f4f4f4")
    main_frame.pack(pady=20)

    image_path = resource_path("fatih.png")  # Dosya adı düzeltildi (küçük harfli)

    try:
        img = Image.open(image_path)
        img = img.resize((250, 250))
        photo = ImageTk.PhotoImage(img)
        label_img = tk.Label(main_frame, image=photo, bg="#f4f4f4")
        label_img.image = photo
        label_img.pack(pady=5)
    except:
        messagebox.showerror("Hata", "fatih.png bulunamadı!")

    tk.Label(main_frame, text="Ne Arıyorsunuz ?", font=("Segoe UI", 11, "bold"), bg="#f4f4f4").pack(pady=(20, 5))

    search_entry = tk.Entry(main_frame, font=("Segoe UI", 12), width=40, bd=2, relief="groove")
    search_entry.pack(pady=5)

    button_image_path = resource_path("fatih_buton.png")
    try:
        button_image = Image.open(button_image_path)
        button_image = button_image.resize((200, 60))
        button_photo = ImageTk.PhotoImage(button_image)

        search_button = tk.Button(
            main_frame,
            image=button_photo,
            borderwidth=0,
            highlightthickness=0,
            bd=0,
            command=start_scraping,
            cursor="hand2",
            bg="#f4f4f4",
            activebackground="#f4f4f4"
        )
        search_button.image = button_photo
        search_button.pack(pady=10)
    except:
        messagebox.showerror("Hata", "fatih_buton.png bulunamadı!")

    progress_label = tk.Label(main_frame, text="İlerleme: 0/0", font=("Segoe UI", 10), bg="#f4f4f4")
    progress_label.pack(pady=5)

    progress_bar = ttk.Progressbar(main_frame, length=300, mode="determinate")
    progress_bar.pack(pady=5)

    root.mainloop()

def show_password_screen():
    password_window = tk.Tk()
    password_window.title("Giriş")
    password_window.geometry("300x150")
    password_window.configure(bg="#ffffff")

    label = tk.Label(password_window, text="Şifreyi girin:", font=("Segoe UI", 12), bg="#ffffff")
    label.pack(pady=10)

    password_entry = tk.Entry(password_window, show="*", font=("Segoe UI", 12), width=25)
    password_entry.pack()

    def check_password():
        if password_entry.get() == "1234":
            password_window.destroy()
            launch_main_app()
        else:
            messagebox.showerror("Hatalı", "Yanlış şifre!")

    login_button = tk.Button(password_window, text="Giriş", command=check_password,
                             font=("Segoe UI", 11, "bold"), bg="#dbeafe", fg="#1e3a8a")
    login_button.pack(pady=10)

    password_window.mainloop()

# 🔐 Başlangıç
show_password_screen()
