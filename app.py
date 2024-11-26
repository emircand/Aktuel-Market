import subprocess
import tkinter as tk
from tkinter import scrolledtext, ttk

def run_data_scraper(category, marketplace):
    process = subprocess.Popen(['python', 'data_scraper.py', category, marketplace], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in process.stdout:
        output_text.insert(tk.END, line)
        output_text.see(tk.END)
        root.update_idletasks()
    for line in process.stderr:
        output_text.insert(tk.END, "\nError: " + line)
        output_text.see(tk.END)
        root.update_idletasks()

def on_run_button_click():
    output_text.delete(1.0, tk.END)
    category = category_var.get()
    marketplace = marketplace_var.get()
    run_data_scraper(category, marketplace)

# Create the main window
root = tk.Tk()
root.title("Data Scraper")

# Create dropdown for category selection
category_var = tk.StringVar()
category_label = tk.Label(root, text="Kategori Seçin:")
category_label.pack(pady=5)
category_dropdown = ttk.Combobox(root, textvariable=category_var)
category_dropdown['values'] = sorted(['içecek', 'meyve sebze', 'et ürünleri',
                        'süt ürünleri kahvaltılık', 'fırın', 'temel gıda', 
                        'atıştırmalık', 'donuk ürünler', 'dondurma', 
                        'temizlik ürünleri', 'kişisel bakım', 'kağıt ürünleri', 
                        'anne bebek', 'ev yaşam', 'kırtasiye', 'evcil hayvan'])
category_dropdown.pack(pady=5)

# Create dropdown for marketplace selection
marketplace_var = tk.StringVar()
marketplace_label = tk.Label(root, text="Market Seçin:")
marketplace_label.pack(pady=5)
marketplace_dropdown = ttk.Combobox(root, textvariable=marketplace_var)
marketplace_dropdown['values'] = sorted(['A101', 'Migros', 'Şok'])
marketplace_dropdown.pack(pady=5)

# Create a button to run the data scraper
run_button = tk.Button(root, text="Veri Çekmeye Başla", command=on_run_button_click)
run_button.pack(pady=10)

# Create a scrolled text widget to display the output
output_text = scrolledtext.ScrolledText(root, width=80, height=20)
output_text.pack(pady=10)

# Start the Tkinter event loop
root.mainloop()
