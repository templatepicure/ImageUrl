def mail_sender_main():
    print("Toplu mail gönderici çalıştı!")  # Buraya kendi gönderme kodunu koyacaksın
import os
import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, Text, Label, Entry
from tkinter import ttk
import requests
import time
import webbrowser
import tempfile

from PIL import Image, ImageTk

def load_logo():
    try:
        image = Image.open("logo.png")  # logo.png dosyasını scriptle aynı dizine koyun
        image = image.resize((500, 500), Image.LANCZOS)  # Boyutları ihtiyaca göre ayarlayın
        return ImageTk.PhotoImage(image)
    except Exception as e:
        print("Logo yüklenemedi:", e)
        return None
# Veritabanı oluşturma
conn = sqlite3.connect("app_data.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS excel_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    filepath TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    filepath TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS email_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    opened INTEGER DEFAULT 0,
    clicked INTEGER DEFAULT 0,
    hard_bounce INTEGER DEFAULT 0,
    soft_bounce INTEGER DEFAULT 0
)
""")
conn.commit()
conn.close()

selected_excel = None
selected_template = None
email = None
api_key = None
webhook_url = None


def login():
    global email, api_key, webhook_url
    login_window = tk.Toplevel(root)
    login_window.title("Giriş Yap")
    login_window.geometry("400x250")
    login_window.resizable(False, False)

    tk.Label(login_window, text="E-posta Gönderme Uygulaması", font=('Arial', 14, 'bold')).pack(pady=10)

    frame = tk.Frame(login_window)
    frame.pack(pady=10)

    email_label = tk.Label(frame, text="E-posta Adresi:", font=('Arial', 10))
    email_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
    email_entry = tk.Entry(frame, font=('Arial', 10), width=30)
    email_entry.grid(row=0, column=1, padx=5, pady=5)

    api_label = tk.Label(frame, text="SendGrid API Anahtarı:", font=('Arial', 10))
    api_label.grid(row=1, column=0, padx=5, pady=5, sticky="e")
    api_entry = tk.Entry(frame, font=('Arial', 10), width=30)
    api_entry.grid(row=1, column=1, padx=5, pady=5)

    webhook_label = tk.Label(frame, text="Webhook URL:", font=('Arial', 10))
    webhook_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
    webhook_entry = tk.Entry(frame, font=('Arial', 10), width=30)
    webhook_entry.grid(row=2, column=1, padx=5, pady=5)

    def submit():
        global email, api_key, webhook_url
        email = email_entry.get()
        api_key = api_entry.get()
        webhook_url = webhook_entry.get()
        if email and api_key and webhook_url:
            messagebox.showinfo("Başarılı", "Giriş başarılı!")
            login_window.destroy()
        else:
            messagebox.showwarning("Uyarı", "Lütfen tüm alanları doldurun!")

    btn_frame = tk.Frame(login_window)
    btn_frame.pack(pady=10)

    submit_button = tk.Button(btn_frame, text="Giriş Yap", command=submit,
                              font=('Arial', 10), width=15, bg="#4CAF50", fg="white")
    submit_button.pack(pady=5)


def send_email_via_sendgrid(subject, body, recipient):
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{"to": [{"email": recipient}]}],
        "from": {"email": email},
        "subject": subject,
        "content": [{"type": "text/html", "value": body}]
    }
    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 202:
        print("🚫 Hata:", response.status_code)
        print("📨 Detay:", response.text)

    return response.status_code == 202


def upload_excel():
    try:
        filepath = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if filepath:
            filename = os.path.basename(filepath)
            conn = sqlite3.connect("app_data.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO excel_files (filename, filepath) VALUES (?, ?)", (filename, filepath))
            conn.commit()
            conn.close()
            messagebox.showinfo("Başarılı", f"{filename} başarıyla yüklendi!")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def upload_template():
    try:
        filepath = filedialog.askopenfilename(filetypes=[("HTML Files", "*.html")])
        if filepath:
            filename = os.path.basename(filepath)
            conn = sqlite3.connect("app_data.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO templates (filename, filepath) VALUES (?, ?)", (filename, filepath))
            conn.commit()
            conn.close()
            messagebox.showinfo("Başarılı", f"{filename} başarıyla yüklendi!")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def select_excel():
    global selected_excel
    try:
        conn = sqlite3.connect("app_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT filename, filepath FROM excel_files")
        files = cursor.fetchall()
        conn.close()

        def set_selected():
            global selected_excel
            index = listbox.curselection()
            if index:
                selected_excel = files[index[0]][1]
                messagebox.showinfo("Seçildi", f"Seçilen Excel: {files[index[0]][0]}")
                display_excel_data(selected_excel)
            library_window.destroy()

        library_window = tk.Toplevel(root)
        library_window.title("Excel Kütüphanesi")
        library_window.geometry("500x400")

        search_frame = tk.Frame(library_window)
        search_frame.pack(pady=10)

        search_entry = tk.Entry(search_frame, width=40, font=('Arial', 10))
        search_entry.pack(side=tk.LEFT, padx=5)

        search_button = tk.Button(search_frame, text="Ara",
                                  command=lambda: search_files(listbox, "excel_files", search_entry),
                                  font=('Arial', 10), width=10)
        search_button.pack(side=tk.LEFT, padx=5)

        listbox = tk.Listbox(library_window, font=('Arial', 10), height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for file in files:
            listbox.insert(tk.END, file[0])

        btn_frame = tk.Frame(library_window)
        btn_frame.pack(pady=10)

        select_button = tk.Button(btn_frame, text="Seç", command=set_selected,
                                  font=('Arial', 10), width=15, bg="#2196F3", fg="white")
        select_button.pack(side=tk.LEFT, padx=10)

        delete_button = tk.Button(btn_frame, text="Sil", command=lambda: delete_file(listbox, "excel_files"),
                                  font=('Arial', 10), width=15, bg="#f44336", fg="white")
        delete_button.pack(side=tk.LEFT, padx=10)

    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def select_template():
    global selected_template
    try:
        conn = sqlite3.connect("app_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT filename, filepath FROM templates")
        files = cursor.fetchall()
        conn.close()

        def set_selected():
            global selected_template
            index = listbox.curselection()
            if index:
                selected_template = files[index[0]][1]
                messagebox.showinfo("Seçildi", f"Seçilen Şablon: {files[index[0]][0]}")
            library_window.destroy()

        library_window = tk.Toplevel(root)
        library_window.title("Şablon Kütüphanesi")
        library_window.geometry("500x400")

        search_frame = tk.Frame(library_window)
        search_frame.pack(pady=10)

        search_entry = tk.Entry(search_frame, width=40, font=('Arial', 10))
        search_entry.pack(side=tk.LEFT, padx=5)

        search_button = tk.Button(search_frame, text="Ara",
                                  command=lambda: search_files(listbox, "templates", search_entry),
                                  font=('Arial', 10), width=10)
        search_button.pack(side=tk.LEFT, padx=5)

        listbox = tk.Listbox(library_window, font=('Arial', 10), height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        for file in files:
            listbox.insert(tk.END, file[0])

        btn_frame = tk.Frame(library_window)
        btn_frame.pack(pady=10)

        select_button = tk.Button(btn_frame, text="Seç", command=set_selected,
                                  font=('Arial', 10), width=15, bg="#2196F3", fg="white")
        select_button.pack(side=tk.LEFT, padx=10)

        delete_button = tk.Button(btn_frame, text="Sil", command=lambda: delete_file(listbox, "templates"),
                                  font=('Arial', 10), width=15, bg="#f44336", fg="white")
        delete_button.pack(side=tk.LEFT, padx=10)

    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def edit_template():
    try:
        if not selected_template:
            messagebox.showerror("Hata", "Lütfen bir şablon seçin!")
            return

        editor_window = tk.Toplevel(root)
        editor_window.title("Şablon Düzenle")
        editor_window.geometry("800x600")

        with open(selected_template, "r", encoding="utf-8") as file:
            content = file.read()

        text_frame = tk.Frame(editor_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_area = tk.Text(text_frame, height=20, width=60, font=('Arial', 10), yscrollcommand=scrollbar.set)
        text_area.insert(tk.END, content)
        text_area.pack(fill=tk.BOTH, expand=True)

        scrollbar.config(command=text_area.yview)

        btn_frame = tk.Frame(editor_window)
        btn_frame.pack(pady=10)

        def save_changes():
            with open(selected_template, "w", encoding="utf-8") as file:
                file.write(text_area.get("1.0", tk.END))
            messagebox.showinfo("Başarılı", "Şablon güncellendi!")
            editor_window.destroy()

        save_button = tk.Button(btn_frame, text="Kaydet", command=save_changes,
                                font=('Arial', 10), width=15, bg="#4CAF50", fg="white")
        save_button.pack(side=tk.LEFT, padx=10)

        preview_button = tk.Button(btn_frame, text="Ön İzleme",
                                   command=lambda: preview_from_editor(text_area.get("1.0", tk.END)),
                                   font=('Arial', 10), width=15, bg="#FF9800", fg="white")
        preview_button.pack(side=tk.LEFT, padx=10)

    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def preview_from_editor(content):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        webbrowser.open(f"file://{temp_file_path}")
    except Exception as e:
        messagebox.showerror("Hata", f"Ön izleme oluşturulurken bir hata oluştu: {e}")


def display_excel_data(filepath):
    try:
        df = pd.read_excel(filepath)
        email_listbox.delete(0, tk.END)
        if 'Email' in df.columns:
            for email in df['Email']:
                email_listbox.insert(tk.END, email)
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def toggle_manual_entry():
    try:
        if use_template_var.get():
            subject_entry.config(state=tk.NORMAL)
            body_text.config(state=tk.DISABLED)
            select_template_button.config(state=tk.NORMAL)
            edit_template_button.config(state=tk.NORMAL)
        else:
            subject_entry.config(state=tk.NORMAL)
            body_text.config(state=tk.NORMAL)
            select_template_button.config(state=tk.DISABLED)
            edit_template_button.config(state=tk.DISABLED)
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def send_bulk_email():
    try:
        if not selected_excel:
            messagebox.showerror("Hata", "Lütfen bir Excel dosyası seçin!")
            return

        if use_template_var.get() and not selected_template:
            messagebox.showerror("Hata", "Lütfen bir şablon seçin!")
            return

        subject = subject_entry.get()
        if use_template_var.get():
            with open(selected_template, "r", encoding="utf-8") as file:
                body = file.read()
        else:
            body = body_text.get("1.0", tk.END)

        df = pd.read_excel(selected_excel)
        if 'Email' not in df.columns:
            messagebox.showerror("Hata", "Excel dosyasında 'Email' sütunu bulunamadı!")
            return

        try:
            emails_per_minute = int(emails_per_minute_entry.get())
            if emails_per_minute <= 0:
                raise ValueError("Geçersiz değer")
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli bir sayı girin!")
            return

        progress_window = tk.Toplevel(root)
        progress_window.title("E-posta Gönderiliyor...")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)

        progress_label = tk.Label(progress_window, text="0/0", font=('Arial', 12))
        progress_label.pack(pady=10)

        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="determinate")
        progress_bar.pack(pady=10)
        progress_bar["maximum"] = len(df)

        status_label = tk.Label(progress_window, text="", font=('Arial', 10))
        status_label.pack(pady=5)

        progress_window.update()

        sent_count = 0
        failed_count = 0

        for index, recipient in enumerate(df['Email']):
            try:
                if email and api_key:
                    if send_email_via_sendgrid(subject, body, recipient):
                        sent_count += 1
                        status = "Başarılı"
                    else:
                        failed_count += 1
                        status = "Başarısız"
                else:
                    sent_count += 1
                    status = "Simüle Edildi"

                progress_label.config(text=f"{index + 1}/{len(df)}")
                status_label.config(text=f"Son durum: {recipient} - {status}")
                progress_bar["value"] = index + 1
                progress_window.update()

                if (index + 1) % emails_per_minute == 0:
                    time.sleep(60)
            except Exception as e:
                failed_count += 1
                print(f"{recipient} adresine e-posta gönderilirken hata oluştu: {e}")

        progress_window.destroy()
        messagebox.showinfo("Sonuç",
                            f"{sent_count} e-posta başarıyla gönderildi.\n{failed_count} e-posta gönderilemedi.")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def search_files(listbox, table_name, search_entry):
    try:
        search_term = search_entry.get().lower()
        conn = sqlite3.connect("app_data.db")
        cursor = conn.cursor()
        cursor.execute(f"SELECT filename FROM {table_name} WHERE filename LIKE ?", ('%' + search_term + '%',))
        files = cursor.fetchall()
        conn.close()

        listbox.delete(0, tk.END)
        for file in files:
            listbox.insert(tk.END, file[0])
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def delete_file(listbox, table_name):
    try:
        selected_item = listbox.curselection()
        if selected_item:
            selected_filename = listbox.get(selected_item)
            conn = sqlite3.connect("app_data.db")
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table_name} WHERE filename = ?", (selected_filename,))
            conn.commit()
            conn.close()
            listbox.delete(selected_item)
            messagebox.showinfo("Başarılı", "Dosya silindi!")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def track_campaign():
    try:
        filepath = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx")])
        if not filepath:
            return

        df = pd.read_excel(filepath)
        if 'Email' not in df.columns:
            messagebox.showerror("Hata", "Excel dosyasında 'Email' sütunu bulunamadı!")
            return

        conn = sqlite3.connect("app_data.db")
        cursor = conn.cursor()
        tracking_data = []
        for recipient in df['Email']:
            cursor.execute("SELECT opened, clicked, hard_bounce, soft_bounce FROM email_tracking WHERE email = ?",
                           (recipient,))
            result = cursor.fetchone()
            if result:
                opened = "Evet" if result[0] else "Hayır"
                clicked = "Evet" if result[1] else "Hayır"
                hard_bounce = "Evet" if result[2] else "Hayır"
                soft_bounce = "Evet" if result[3] else "Hayır"
                tracking_data.append([recipient, opened, clicked, hard_bounce, soft_bounce])
        conn.close()

        output_df = pd.DataFrame(tracking_data, columns=["E-posta", "Açıldı", "Tıklandı", "Hard Bounce", "Soft Bounce"])
        output_filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if output_filepath:
            output_df.to_excel(output_filepath, index=False)
            messagebox.showinfo("Başarılı", f"Takip verileri kaydedildi!")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def preview_email():
    try:
        if use_template_var.get() and selected_template:
            with open(selected_template, "r", encoding="utf-8") as file:
                content = file.read()
        else:
            content = body_text.get("1.0", tk.END)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        webbrowser.open(f"file://{temp_file_path}")

    except Exception as e:
        messagebox.showerror("Hata", f"Ön izleme oluşturulurken bir hata oluştu: {e}")


def send_test_email():
    try:
        test_window = tk.Toplevel(root)
        test_window.title("Test Gönderimi")
        test_window.geometry("400x200")
        test_window.resizable(False, False)

        tk.Label(test_window, text="Test E-posta Adresi:", font=('Arial', 12)).pack(pady=10)

        test_email_entry = tk.Entry(test_window, font=('Arial', 12), width=30)
        test_email_entry.pack(pady=5)

        def send_test():
            test_email = test_email_entry.get()
            if not test_email:
                messagebox.showwarning("Uyarı", "Lütfen bir e-posta adresi girin!")
                return

            subject = subject_entry.get()
            if use_template_var.get() and selected_template:
                with open(selected_template, "r", encoding="utf-8") as file:
                    body = file.read()
            else:
                body = body_text.get("1.0", tk.END)

            if email and api_key:
                if send_email_via_sendgrid(subject, body, test_email):
                    messagebox.showinfo("Başarılı", "Test e-postası başarıyla gönderildi!")
                else:
                    messagebox.showerror("Hata", "Test e-postası gönderilemedi!")
            else:
                messagebox.showinfo("Test Gönderimi", "Test e-postası simüle edildi!")

            test_window.destroy()

        btn_frame = tk.Frame(test_window)
        btn_frame.pack(pady=15)

        send_button = tk.Button(btn_frame, text="Gönder", command=send_test,
                                font=('Arial', 12), width=15, bg="#4CAF50", fg="white")
        send_button.pack(side=tk.LEFT, padx=10)

        cancel_button = tk.Button(btn_frame, text="İptal", command=test_window.destroy,
                                  font=('Arial', 12), width=15, bg="#f44336", fg="white")
        cancel_button.pack(side=tk.LEFT, padx=10)

    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def edit_selected_email():
    try:
        selected_index = email_listbox.curselection()
        if selected_index:
            selected_email = email_listbox.get(selected_index)
            edit_window = tk.Toplevel(root)
            edit_window.title("E-posta Düzenle")
            edit_window.geometry("400x150")
            edit_window.resizable(False, False)

            tk.Label(edit_window, text="E-posta Adresi:", font=('Arial', 12)).pack(pady=10)

            email_entry = tk.Entry(edit_window, font=('Arial', 12), width=30)
            email_entry.insert(0, selected_email)
            email_entry.pack(pady=5)

            def save_changes():
                new_email = email_entry.get()
                if new_email:
                    email_listbox.delete(selected_index)
                    email_listbox.insert(selected_index, new_email)
                    edit_window.destroy()
                else:
                    messagebox.showwarning("Uyarı", "E-posta adresi boş olamaz!")

            btn_frame = tk.Frame(edit_window)
            btn_frame.pack(pady=10)

            save_button = tk.Button(btn_frame, text="Kaydet", command=save_changes,
                                    font=('Arial', 12), width=15, bg="#4CAF50", fg="white")
            save_button.pack(side=tk.LEFT, padx=10)

            cancel_button = tk.Button(btn_frame, text="İptal", command=edit_window.destroy,
                                      font=('Arial', 12), width=15, bg="#f44336", fg="white")
            cancel_button.pack(side=tk.LEFT, padx=10)
        else:
            messagebox.showwarning("Uyarı", "Lütfen bir e-posta adresi seçin!")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


def delete_selected_email():
    try:
        selected_index = email_listbox.curselection()
        if selected_index:
            email_listbox.delete(selected_index)
        else:
            messagebox.showwarning("Uyarı", "Lütfen bir e-posta adresi seçin!")
    except Exception as e:
        messagebox.showerror("Hata", f"Bir hata oluştu: {e}")


# Ana pencere oluşturma
root = tk.Tk()
root.title("E-posta Gönderme Uygulaması")
root.geometry("1000x700")
root.state('zoomed')  # Tam ekran başlat

# Grid yapılandırması
for i in range(15):
    root.grid_rowconfigure(i, weight=1)
for i in range(2):
    root.grid_columnconfigure(i, weight=1)

# Giriş penceresini başlat
login()

# Sol panel (Dosya işlemleri)
left_frame = tk.Frame(root, bd=2, relief=tk.RAISED, padx=10, pady=10)
left_frame.grid(row=0, column=0, rowspan=15, sticky="nsew", padx=5, pady=5)
left_frame.grid_propagate(False)

tk.Label(left_frame, text="Dosya İşlemleri", font=('Arial', 12, 'bold')).pack(pady=10)

upload_excel_button = tk.Button(left_frame, text="Excel Yükle", command=upload_excel,
                                font=('Arial', 12), width=20, height=2, bg="#2196F3", fg="white")
upload_excel_button.pack(pady=5, fill=tk.X)

upload_template_button = tk.Button(left_frame, text="Şablon Yükle", command=upload_template,
                                   font=('Arial', 12), width=20, height=2, bg="#2196F3", fg="white")
upload_template_button.pack(pady=5, fill=tk.X)

excel_library_button = tk.Button(left_frame, text="Excel Kütüphanesi", command=select_excel,
                                 font=('Arial', 12), width=20, height=2, bg="#FF9800", fg="white")
excel_library_button.pack(pady=5, fill=tk.X)

template_library_button = tk.Button(left_frame, text="Şablon Kütüphanesi", command=select_template,
                                    font=('Arial', 12), width=20, height=2, bg="#FF9800", fg="white")
template_library_button.pack(pady=5, fill=tk.X)

tk.Label(left_frame, text="E-posta Ayarları", font=('Arial', 12, 'bold')).pack(pady=(20, 5))

use_template_var = tk.BooleanVar()
use_template_checkbox = tk.Checkbutton(left_frame, text="Şablon Kullan", variable=use_template_var,
                                       command=toggle_manual_entry, font=('Arial', 12))
use_template_checkbox.pack(pady=5)

select_template_button = tk.Button(left_frame, text="Şablon Seç", command=select_template,
                                   font=('Arial', 12), width=20, height=2, bg="#9C27B0", fg="white")
select_template_button.pack(pady=5, fill=tk.X)

edit_template_button = tk.Button(left_frame, text="Şablon Düzenle", command=edit_template,
                                 font=('Arial', 12), width=20, height=2, bg="#9C27B0", fg="white")
edit_template_button.pack(pady=5, fill=tk.X)
# Logo ekleme (Şablon Düzenle butonunun altına)
logo_image = load_logo()
if logo_image:
    logo_label = tk.Label(left_frame, image=logo_image, bg="#f0f0f0")
    logo_label.image = logo_image
    logo_label.pack(pady=(20, 10), fill=tk.X)  # Üstte 20, altta 10 piksel boşluk
# Sağ panel (E-posta içeriği ve gönderim)
right_frame = tk.Frame(root, bd=2, relief=tk.RAISED, padx=10, pady=10)
right_frame.grid(row=0, column=1, rowspan=15, sticky="nsew", padx=5, pady=5)
right_frame.grid_propagate(False)

tk.Label(right_frame, text="E-posta Gönderimi", font=('Arial', 12, 'bold')).pack(pady=10)

select_excel_button = tk.Button(right_frame, text="Excel Seç", command=select_excel,
                                font=('Arial', 12), width=20, height=2, bg="#2196F3", fg="white")
select_excel_button.pack(pady=5, fill=tk.X)

tk.Label(right_frame, text="E-posta Listesi", font=('Arial', 12)).pack(pady=5)

email_list_frame = tk.Frame(right_frame)
email_list_frame.pack(fill=tk.BOTH, expand=True)

scrollbar = tk.Scrollbar(email_list_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

email_listbox = tk.Listbox(email_list_frame, font=('Arial', 11), yscrollcommand=scrollbar.set)
email_listbox.pack(fill=tk.BOTH, expand=True)

scrollbar.config(command=email_listbox.yview)

email_btn_frame = tk.Frame(right_frame)
email_btn_frame.pack(pady=5)

edit_email_button = tk.Button(email_btn_frame, text="Düzenle", command=edit_selected_email,
                              font=('Arial', 10), width=10, bg="#4CAF50", fg="white")
edit_email_button.pack(side=tk.LEFT, padx=5)

delete_email_button = tk.Button(email_btn_frame, text="Sil", command=delete_selected_email,
                                font=('Arial', 10), width=10, bg="#f44336", fg="white")
delete_email_button.pack(side=tk.LEFT, padx=5)

tk.Label(right_frame, text="E-posta Ayarları", font=('Arial', 12)).pack(pady=5)

emails_per_minute_frame = tk.Frame(right_frame)
emails_per_minute_frame.pack(pady=5)

tk.Label(emails_per_minute_frame, text="Dakikada Gönderim:", font=('Arial', 10)).pack(side=tk.LEFT)

emails_per_minute_entry = tk.Entry(emails_per_minute_frame, font=('Arial', 10), width=5)
emails_per_minute_entry.pack(side=tk.LEFT, padx=5)
emails_per_minute_entry.insert(0, "60")

tk.Label(right_frame, text="E-posta İçeriği", font=('Arial', 12)).pack(pady=5)

subject_frame = tk.Frame(right_frame)
subject_frame.pack(fill=tk.X, pady=5)

tk.Label(subject_frame, text="Konu:", font=('Arial', 10)).pack(side=tk.LEFT)

subject_entry = tk.Entry(subject_frame, font=('Arial', 10))
subject_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

body_frame = tk.Frame(right_frame)
body_frame.pack(fill=tk.BOTH, expand=True)

scrollbar_body = tk.Scrollbar(body_frame)
scrollbar_body.pack(side=tk.RIGHT, fill=tk.Y)

body_text = tk.Text(body_frame, font=('Arial', 10), yscrollcommand=scrollbar_body.set)
body_text.pack(fill=tk.BOTH, expand=True)

scrollbar_body.config(command=body_text.yview)

action_btn_frame = tk.Frame(right_frame)
action_btn_frame.pack(pady=10)

preview_button = tk.Button(action_btn_frame, text="Ön İzleme", command=preview_email,
                           font=('Arial', 10), width=15, bg="#FF9800", fg="white")
preview_button.pack(side=tk.LEFT, padx=5)

test_email_button = tk.Button(action_btn_frame, text="Test Gönder", command=send_test_email,
                              font=('Arial', 10), width=15, bg="#607D8B", fg="white")
test_email_button.pack(side=tk.LEFT, padx=5)

send_email_button = tk.Button(action_btn_frame, text="Toplu Gönder", command=send_bulk_email,
                              font=('Arial', 10), width=15, bg="#4CAF50", fg="white")
send_email_button.pack(side=tk.LEFT, padx=5)

track_campaign_button = tk.Button(right_frame, text="Kampanya Takip", command=track_campaign,
                                  font=('Arial', 12), width=20, height=2, bg="#795548", fg="white")
track_campaign_button.pack(pady=10, fill=tk.X)

# Başlangıçta doğru durumu ayarla
toggle_manual_entry()

root.mainloop()