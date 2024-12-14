import subprocess
import tkinter as tk
from tkinter import scrolledtext, ttk
import json

def load_categories():
    with open('subcategory_mapper.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['categories']

def run_data_scraper(category_path, marketplace, browser):
    process = subprocess.Popen(['python', 'data_scraper.py', category_path[0], marketplace, browser] + category_path[1:], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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
    selected_item = category_tree.selection()
    if selected_item:
        category_path = []
        item = selected_item[0]
        while item:
            category_path.insert(0, category_tree.item(item, 'text'))
            item = category_tree.parent(item)
        marketplace = marketplace_var.get()
        browser = browser_var.get()
        run_data_scraper(category_path, marketplace, browser)

# Load categories from subcategory_mapper.json
categories = load_categories()

# Create the main window
root = tk.Tk()
root.title("Data Scraper")

# Create a treeview for category selection
category_label = tk.Label(root, text="Kategori Seçin:")
category_label.pack(pady=5)
category_tree = ttk.Treeview(root)
category_tree.pack(pady=5, fill=tk.BOTH, expand=True)

# Populate the treeview with categories and subcategories
def populate_treeview(tree, parent, categories):
    for category, data in categories.items():
        node = tree.insert(parent, 'end', text=category)
        if 'subcategories' in data:
            populate_treeview(tree, node, data['subcategories'])

populate_treeview(category_tree, '', categories)

# Create dropdown for marketplace selection
marketplace_var = tk.StringVar()
marketplace_label = tk.Label(root, text="Market Seçin:")
marketplace_label.pack(pady=5)
marketplace_dropdown = ttk.Combobox(root, textvariable=marketplace_var)
marketplace_dropdown['values'] = sorted(['Migros'])
marketplace_dropdown.pack(pady=5)

# Create dropdown for browser selection
browser_var = tk.StringVar()
browser_label = tk.Label(root, text="Tarayıcı Seçin:")
browser_label.pack(pady=5)
browser_dropdown = ttk.Combobox(root, textvariable=browser_var)
browser_dropdown['values'] = sorted(['Chrome', 'Firefox', 'Edge'])
browser_dropdown.pack(pady=5)

# Create a button to run the data scraper
run_button = tk.Button(root, text="Veri Çekmeye Başla", command=on_run_button_click)
run_button.pack(pady=10)

# Create a scrolled text widget to display the output
output_text = scrolledtext.ScrolledText(root, width=80, height=20)
output_text.pack(pady=10)

# Start the Tkinter event loop
root.mainloop()