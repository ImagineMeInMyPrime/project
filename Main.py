import customtkinter as ctk
import datetime
import os
import csv
import win32print
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

services_file = "services.txt"
check_number_file = "last_check_number.txt"
cash_register_file = "cash_register_number.txt"
settings_file = "settings.txt"
receipts_folder = "Receipts"
csv_file = os.path.join(receipts_folder, "check.csv")
pdf_folder = os.path.join(receipts_folder, "pdfs")

def load_mode():
    if os.path.exists(settings_file):
        with open(settings_file, "r", encoding="utf-8") as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    else:
        with open(settings_file, "w", encoding="utf-8") as f:
            f.write("0")
        return 0

mode = load_mode()

class ReceiptPrinter:
    def __init__(self):
        self.printer_name = win32print.GetDefaultPrinter()
    def print_sale_receipt(self, cash_register_number, order_number, items, mode, receipt_date):
        try:
            hprinter = win32print.OpenPrinter(self.printer_name)
            def enc(s):
                return s.encode("cp852", errors="replace")
            total = sum(price for _, price in items)
            if mode == 0:
                dph = total * 0.21
                base_total = total
                grand_total = total + dph
            else:
                base_total = total / 1.21
                dph = total - base_total
                grand_total = total
            commands = [
                b'\x1B\x40', b'\x1B\x74\x12', b'\x1B\x61\x01', b'\x1B\x21\x30',
                enc("RENOME SPC s.r.o\n"), b'\x1B\x21\x00',
                enc("Hartigova 31/27\n"), enc("130 00 Praha 3 - Žížkov\n"),
                enc("IČ: 05814812, DIČ: CZ05814812\n"), enc("="*30 + "\n"),
                b'\x1B\x61\x00', enc(f"Číslo pokladny: #{cash_register_number}\n"),
                enc(f"Číslo účtenky: #{order_number}\n"),
                enc(f"Datum: {receipt_date}\n"),
                enc(f"Zaplaceno v hotovosti\n"),
                enc("-"*30 + "\n"), b'\x1B\x45\x01', enc("Název služby           Cena\n"),
                b'\x1B\x45\x00', enc("-"*30 + "\n")
            ]
            for name, price in items:
                commands.append(enc(f"{name:<20} {price:>7.2f} Kč\n"))
            commands.extend([
                enc("-"*30 + "\n"),
                enc(f"Cena (bez DPH): {base_total:.2f} Kč\n"),
                enc(f"DPH 21%: {dph:.2f} Kč\n"),
                enc(f"Cena s DPH: {grand_total:.2f} Kč\n"),
                enc("="*30 + "\n"), b'\x1D\x56\x41\x00'
            ])
            raw_data = b"".join(commands)
            win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, raw_data)
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            win32print.ClosePrinter(hprinter)
        except Exception as e:
            print(f"Chyba tisku {e}")

printer = ReceiptPrinter()

if os.path.exists(services_file):
    with open(services_file, "r", encoding="utf-8") as f:
        services_list = [line.strip() for line in f if line.strip()]
else:
    services_list = ["Překlad z angličtiny", "Překlad z Němčiny", "Překlad z čínštiny"]
    with open(services_file, "w", encoding="utf-8") as f:
        for service in services_list:
            f.write(service + "\n")

def load_check_number():
    if os.path.exists(check_number_file):
        with open(check_number_file, "r", encoding="utf-8") as f:
            try:
                return int(f.read().strip())
            except:
                return 1
    else:
        with open(check_number_file, "w", encoding="utf-8") as f:
            f.write("1")
        return 1

def save_check_number(number):
    with open(check_number_file, "w", encoding="utf-8") as f:
        f.write(str(number))

def load_cash_register_number():
    if os.path.exists(cash_register_file):
        with open(cash_register_file, "r", encoding="utf-8") as f:
            try:
                return int(f.read().strip())
            except:
                return 1
    else:
        with open(cash_register_file, "w", encoding="utf-8") as f:
            f.write("1")
        return 1

root = ctk.CTk()
root.title("Systém účtenek")
root.geometry("800x600")

cash_register_number = load_cash_register_number()
current_check_number = load_check_number()
today_date = datetime.datetime.now().strftime("%d.%m.%Y")

ctk.CTkLabel(root, text="Číslo pokladny:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
register_label = ctk.CTkLabel(root, text=str(cash_register_number), font=("Arial", 13, "bold"))
register_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")

ctk.CTkLabel(root, text="Číslo účtenky:").grid(row=0, column=2, padx=10, pady=10, sticky="w")
number_entry = ctk.CTkEntry(root, width=120, corner_radius=10)
number_entry.grid(row=0, column=3, padx=10, pady=10, sticky="w")
number_entry.insert(0, str(current_check_number))
number_entry.configure(state="readonly")

ctk.CTkLabel(root, text="Datum:").grid(row=0, column=4, padx=10, pady=10, sticky="w")
date_entry = ctk.CTkEntry(root, width=120, corner_radius=10)
date_entry.grid(row=0, column=5, padx=10, pady=10, sticky="w")
date_entry.insert(0, today_date)

services_container = ctk.CTkFrame(root, corner_radius=10, fg_color="#f0f0f0")
services_container.grid(row=1, column=0, columnspan=6, padx=10, pady=10, sticky="we")

service_frames = []

# --- Kompaktní a zarovnaný blok Bez DPH / DPH / Celkem ---
# --- Kompaktní a zarovnaný blok Bez DPH / DPH / Celkem с копейками ---

summary_frame = ctk.CTkFrame(root, fg_color="transparent")
summary_frame.grid(row=2, column=0, columnspan=6, padx=10, pady=0, sticky="w")

base_label = ctk.CTkLabel(summary_frame, text="Bez DPH: 0.00 Kč", font=("Arial", 13), padx=0, pady=0)
base_label.grid(row=0, column=0, sticky="w")

dph_label = ctk.CTkLabel(summary_frame, text="DPH 21%: 0.00 Kč", font=("Arial", 13), padx=0, pady=0)
dph_label.grid(row=1, column=0, sticky="w")

ctk.CTkLabel(summary_frame, text="Celkem:", font=("Arial", 13, "bold"), padx=0, pady=0).grid(row=2, column=0, sticky="w")
total_label = ctk.CTkLabel(summary_frame, text="0.00 Kč", font=("Arial", 14, "bold"), padx=0, pady=0)
total_label.grid(row=2, column=1, padx=10, sticky="w")




def update_total():
    total = 0
    for frame in service_frames:
        try:
            price = float(frame['price'].get())
            total += price
        except ValueError:
            continue
    if mode == 0:
        dph = total * 0.21
        grand_total = total + dph
        base_total = total
    else:
        base_total = total / 1.21
        dph = total - base_total
        grand_total = total

    # --- Обновляем GUI с копейками ---
    base_label.configure(text=f"Bez DPH: {base_total:.2f} Kč")
    dph_label.configure(text=f"DPH 21%: {dph:.2f} Kč")
    total_label.configure(text=f"{grand_total:.2f} Kč")

def add_service_to_file(service_name):
    if not service_name.strip():
        return
    if service_name not in services_list:
        services_list.append(service_name)
        with open(services_file, "a", encoding="utf-8") as f:
            f.write(service_name + "\n")
        for frame in service_frames:
            frame['service_box'].configure(values=services_list)

def add_service_row(service_name="", price=""):
    frame = ctk.CTkFrame(services_container, corner_radius=10, fg_color="#ffffff")
    frame.pack(fill="x", pady=5)
    service_var = ctk.StringVar(value=service_name)
    service_box = ctk.CTkComboBox(frame, variable=service_var, values=services_list, width=250)
    service_box.pack(side="left", padx=5, pady=5)
    price_entry = ctk.CTkEntry(frame, width=100)
    price_entry.pack(side="left", padx=5, pady=5)
    price_entry.insert(0, price)
    price_entry.bind("<KeyRelease>", lambda e: update_total())
    add_button = ctk.CTkButton(
        frame,
        text="Přidat servis",
        width=120,
        height=32,
        corner_radius=10,
        fg_color="#007BFF",
        hover_color="#0056b3",
        text_color="white",
        font=("Arial", 12, "bold"),
        command=lambda: add_service_to_file(service_var.get())
    )
    add_button.pack(side="left", padx=10, pady=5)
    service_frames.append({
        'frame': frame,
        'service': service_var,
        'service_box': service_box,
        'price': price_entry
    })

add_service_row()
update_total()

def save_receipt():
    selected_date = date_entry.get()
    global current_check_number
    number = current_check_number
    if not os.path.exists(receipts_folder):
        os.makedirs(receipts_folder)
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
    if not os.path.exists(csv_file):
        with open(csv_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Datum", "Číslo pokladny", "Číslo účtenky", "Služba", "Cena (bez DPH)", "DPH 21%", "Cena s DPH"])
    items_for_print = []
    total = 0
    for frame in service_frames:
        service = frame['service'].get()
        price = frame['price'].get()
        if not (service and price):
            continue
        try:
            price_val = float(price)
            total += price_val
            items_for_print.append((service, price_val))
        except:
            continue
    if mode == 0:
        dph = total * 0.21
        base_total = total
        grand_total = total + dph
    else:
        base_total = total / 1.21
        dph = total - base_total
        grand_total = total
    with open(csv_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for service, price_val in items_for_print:
            writer.writerow([selected_date, cash_register_number, number, service, f"{base_total:.2f}", f"{dph:.2f}",
                             f"{grand_total:.2f}"])
    if items_for_print:
        printer.print_sale_receipt(
            cash_register_number,
            number,
            items_for_print,
            mode,
            selected_date
        )
    pdf_file = os.path.join(pdf_folder, f"receipt_{number}.pdf")
    c = canvas.Canvas(pdf_file, pagesize=A4)
    pdfmetrics.registerFont(TTFont('FreeMono', 'C:\\Windows\\Fonts\\cour.ttf'))
    c.setFont('FreeMono', 10)
    a6_width, a6_height = 297, 420
    width, height = A4
    x_offset = (width - a6_width)/2
    y_offset = (height + a6_height)/2
    y = y_offset - 20
    c.drawString(x_offset + 20, y, "RENOME SPC s.r.o")
    y -= 20
    c.drawString(x_offset + 20, y, "Hartigova 31/27, 130 00 Praha 3 - Žížkov")
    y -= 20
    c.drawString(x_offset + 20, y, "IČ: 05814812, DIČ: CZ05814812")
    y -= 20
    c.drawString(x_offset + 20, y, f"Číslо pokladny: {cash_register_number}")
    c.drawString(x_offset + 150, y, f"Číslo účtenky: {number}")
    y -= 20
    c.drawString(x_offset + 20, y, f"Datum: {selected_date}")

    y -= 20
    c.drawString(x_offset + 20, y, f"Zaplaceno v hotovosti")
    y -= 20
    c.drawString(x_offset + 20, y, "Služba")
    c.drawString(x_offset + 150, y, "Cena")
    y -= 15
    c.line(x_offset + 20, y, x_offset + 270, y)
    y -= 15
    for service, price_val in items_for_print:
        c.drawString(x_offset + 20, y, service)
        c.drawString(x_offset + 150, y, f"{price_val:.2f} Kč")
        y -= 15
    y -= 10
    c.line(x_offset + 20, y, x_offset + 270, y)
    y -= 15
    c.drawString(x_offset + 20, y, f"Bez DPH: {base_total:.2f} Kč")
    y -= 15
    c.drawString(x_offset + 20, y, f"DPH 21%: {dph:.2f} Kč")
    y -= 15
    c.drawString(x_offset + 20, y, f"Cena s DPH: {grand_total:.2f} Kč")
    c.showPage()
    c.save()
    current_check_number += 1
    number_entry.configure(state="normal")
    number_entry.delete(0, "end")
    number_entry.insert(0, str(current_check_number))
    number_entry.configure(state="readonly")
    for frame in service_frames:
        frame['frame'].destroy()
    service_frames.clear()
    add_service_row()
    update_total()
    save_check_number(current_check_number)

save_button = ctk.CTkButton(root, text="Uložit účtenku", width=180, height=40, corner_radius=15, fg_color="#4CAF50", hover_color="#45a049", command=save_receipt)
save_button.grid(row=3, column=0, columnspan=6, pady=20)

def show_help():
    help_window = ctk.CTkToplevel(root)
    help_window.title("Nápověda")
    help_window.geometry("450x350")
    help_window.resizable(False, False)
    ctk.CTkLabel(help_window, text="Nápověda k systému účtenek", font=("Arial", 16, "bold")).pack(pady=10)
    text = (
        "Jak používat aplikaci:\n\n"
        "Vyberte nebo napište název služby v poli „Služba“.\n"
        "Do pole vedle zadejte cenu služby.\n"
        "Stiskněte „Přidat servis“, pokud chcete službu uložit do seznamu.\n"
        "Klikněte na „Uložit účtenku“, abyste vytvořili účtenku a PDF.\n"
        "Systém automaticky vypočítá DPH a uloží údaje do souboru check.csv.\n\n"
        "Tip: Pokud se služba opakuje často, přidejte ji jednou a bude trvale uložena.\n"
        "========================================================\n"
        "Settings.txt - 0 znamená cena nevčetně DPH, 1 - znamená včetně DPH\n"
        "cash_register.txt je číslo pokladny\n"
        "last_check_number.txt je číslo účtenky\n"
        "services.txt je to seznam vašich služeb\n"
    )
    box = ctk.CTkTextbox(help_window, width=420, height=250, wrap="word")
    box.pack(pady=10)
    box.insert("1.0", text)
    box.configure(state="disabled")

help_button = ctk.CTkButton(root, text="?", width=35, height=35, corner_radius=35, fg_color="#2196F3", hover_color="#1976D2", text_color="white", font=("Arial", 16, "bold"), command=show_help)
help_button.place(x=750, y=20)

root.mainloop()
#круто