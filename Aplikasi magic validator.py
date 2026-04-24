import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os

# =========================
# MAGIC NUMBER DATABASE (DIPERBAIKI UNTUK MP4)
# =========================
MAGIC_NUMBERS = {
    "jpg": ["FFD8FF"],
    "png": ["89504E47"],
    "pdf": ["25504446"],
    "zip": ["504B0304", "504B0506", "504B0708"],
    "mp3": ["494433", "FFFB"],
    "mp4": ["00000018", "00000020", "66747970", "6D703432", "69736F6D", "6D703431", "4D534E56"],  # MP4 magic numbers lengkap
    "exe": ["4D5A"]
}

file_list = []
dark_mode = False

# =========================
# FORMAT HEX
# =========================
def format_hex(hex_string):
    if hex_string == "-" or not hex_string:
        return "-"
    return ' '.join(hex_string[i:i+2] for i in range(0, len(hex_string), 2))

# =========================
# BACA HEADER (BACA LEBIH BANYAK UNTUK MP4)
# =========================
def get_file_header(file_path, bytes_to_read=32):
    try:
        with open(file_path, "rb") as f:
            return f.read(bytes_to_read).hex().upper()
    except:
        return ""

# =========================
# DETEKSI FILE (DIPERBAIKI UNTUK MP4)
# =========================
def detect_file(file_path):
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].replace(".", "").lower()
    header = get_file_header(file_path, 32)  # Baca 32 byte
    
    detected_type = "Unknown"
    detected_magic = "-"
    status = "Tidak Valid"

    # Deteksi khusus untuk MP4 terlebih dahulu (karena bisa di posisi manapun)
    # Cek signature MP4 yang umum
    mp4_signatures = ["66747970", "6D703432", "69736F6D", "6D703431", "4D534E56"]
    for sig in mp4_signatures:
        if sig in header[:16]:  # Cek di 16 byte pertama
            detected_type = "mp4"
            detected_magic = sig
            break
    
    # Jika belum terdeteksi, cek tipe file lain
    if detected_type == "Unknown":
        for filetype, sigs in MAGIC_NUMBERS.items():
            if filetype == "mp4":  # Skip MP4 karena sudah dicek
                continue
            for sig in sigs:
                if header.startswith(sig):
                    detected_type = filetype
                    detected_magic = sig
                    break
            if detected_type != "Unknown":
                break
    
    # Validasi ekstensi
    if detected_type == ext:
        status = "Valid"
    elif detected_type != "Unknown":
        status = "Mismatch"
    else:
        status = "Tidak Terdeteksi"

    # Tampilkan 16 byte pertama (32 digit hex)
    formatted_header = format_hex(header[:32])
    formatted_magic = format_hex(detected_magic) if detected_magic != "-" else "-"

    return filename, ext, formatted_header, formatted_magic, detected_type, status

# =========================
# INSERT TABLE
# =========================
def insert_table(data):
    index = len(tree.get_children())
    tag = "even" if index % 2 == 0 else "odd"
    tree.insert("", "end", values=data, tags=(tag,))

# =========================
# PILIH FILE
# =========================
def select_files():
    files = filedialog.askopenfilenames()
    if not files:
        return
    
    for file in files:
        try:
            data = detect_file(file)
            insert_table(data)
            file_list.append(file)
            print(f"Debug - File: {file}, Detected: {data[4]}, Magic: {data[3]}")  # Debug print
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membaca file:\n{file}\n{str(e)}")
    
    update_status()

# =========================
# UPDATE STATUS
# =========================
def update_status():
    file_count = len(tree.get_children())
    status_label.config(text=f"✅ {file_count} file terdeteksi | Magic Number Checker")

# =========================
# RENAME (TANPA HAPUS)
# =========================
def rename_files():
    new_ext = entry_ext.get().lower().replace(".", "")
    if not new_ext:
        messagebox.showerror("Error", "Masukkan ekstensi baru!")
        return

    selected_items = tree.selection()

    if not selected_items:
        messagebox.showwarning("Peringatan", "Pilih file di tabel terlebih dahulu!")
        return

    success_count = 0
    error_count = 0
    error_messages = []

    for item in selected_items:
        values = tree.item(item, "values")
        if not values:
            continue
            
        filename = values[0]

        for i, file_path in enumerate(file_list):
            if os.path.basename(file_path) == filename:
                base = os.path.splitext(file_path)[0]
                new_name = base + "." + new_ext

                if os.path.exists(new_name):
                    error_count += 1
                    error_messages.append(f"File sudah ada: {new_name}")
                    continue

                try:
                    os.rename(file_path, new_name)
                    file_list[i] = new_name
                    new_data = detect_file(new_name)
                    tree.item(item, values=new_data)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    error_messages.append(f"Gagal rename {filename}: {e}")
                break

    if success_count > 0:
        messagebox.showinfo("Sukses", f"Berhasil mengubah ekstensi {success_count} file!")
    if error_count > 0:
        messagebox.showerror("Error", f"Gagal mengubah {error_count} file:\n" + "\n".join(error_messages[:5]))
    
    update_status()

# =========================
# HAPUS DARI TABEL SAJA
# =========================
def delete_from_table_only():
    selected_items = tree.selection()

    if not selected_items:
        messagebox.showwarning("Peringatan", "Pilih file di tabel terlebih dahulu!")
        return

    confirm = messagebox.askyesno("Konfirmasi Hapus dari Tampilan", 
                                   f"Anda akan menghapus {len(selected_items)} file dari tampilan.\n\n"
                                   "⚠️ File asli TIDAK akan dihapus dari komputer!\n\n"
                                   "Yakin ingin menghapus dari tabel?")
    if not confirm:
        return

    deleted_count = 0
    
    for item in selected_items:
        values = tree.item(item, "values")
        if values:
            filename = values[0]
            
            for i, file_path in enumerate(file_list):
                if os.path.basename(file_path) == filename:
                    file_list.pop(i)
                    break
            
            tree.delete(item)
            deleted_count += 1

    if deleted_count > 0:
        messagebox.showinfo("Sukses", f"✅ Berhasil menghapus {deleted_count} file dari tampilan!\n\nFile asli masih tersimpan di komputer.")
    
    update_status()

# =========================
# HAPUS SEMUA DARI TABEL
# =========================
def clear_all_table():
    if not tree.get_children():
        messagebox.showwarning("Peringatan", "Tabel sudah kosong!")
        return
    
    confirm = messagebox.askyesno("Konfirmasi Hapus Semua", 
                                   f"Anda akan menghapus SEMUA file dari tampilan ({len(tree.get_children())} file).\n\n"
                                   "⚠️ File asli TIDAK akan dihapus dari komputer!\n\n"
                                   "Yakin ingin membersihkan tabel?")
    if not confirm:
        return
    
    tree.delete(*tree.get_children())
    file_list.clear()
    
    messagebox.showinfo("Sukses", f"✅ Berhasil menghapus semua file dari tampilan!\n\nFile asli masih tersimpan di komputer.")
    update_status()

# =========================
# TOGGLE FULLSCREEN
# =========================
def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))

# =========================
# THEME
# =========================
def apply_theme():
    if dark_mode:
        # Dark Mode Colors
        bg_color = "#1e1e2e"
        fg_color = "#ffffff"
        even_bg = "#2d2d3a"
        odd_bg = "#252530"
        header_bg = "#3a3a4a"
        header_fg = "#ffffff"
        button_bg = "#0d6efd"
        button_fg = "#ffffff"
        delete_bg = "#dc3545"
        entry_bg = "#2d2d3a"
        entry_fg = "#ffffff"
        title_bg = "#252530"
        status_bg = "#2d2d3a"
        select_bg = "#0d6efd"
        hover_bg = "#0b5ed7"
    else:
        # Light Mode Colors
        bg_color = "#f8f9fa"
        fg_color = "#212529"
        even_bg = "#ffffff"
        odd_bg = "#f8f9fa"
        header_bg = "#e9ecef"
        header_fg = "#212529"
        button_bg = "#0d6efd"
        button_fg = "#ffffff"
        delete_bg = "#dc3545"
        entry_bg = "#ffffff"
        entry_fg = "#212529"
        title_bg = "#ffffff"
        status_bg = "#e9ecef"
        select_bg = "#0d6efd"
        hover_bg = "#0b5ed7"

    # Configure root window
    root.configure(bg=bg_color)
    frame_main.configure(bg=bg_color)
    
    # Title frame
    title_frame.configure(bg=title_bg)
    title_label.configure(bg=title_bg, fg=fg_color)
    subtitle_label.configure(bg=title_bg, fg="#6c757d" if not dark_mode else "#a0a0b0")
    
    # Control frames
    control_frame.configure(bg=bg_color)
    left_buttons.configure(bg=bg_color)
    right_buttons.configure(bg=bg_color)
    ext_frame.configure(bg=bg_color)
    ext_label.configure(bg=bg_color, fg=fg_color)
    
    # Entry
    entry_ext.configure(bg=entry_bg, fg=entry_fg, insertbackground=fg_color)
    
    # Buttons
    btn_select.configure(bg=button_bg, fg=button_fg, activebackground=hover_bg, 
                        activeforeground="white", relief=tk.FLAT, bd=0)
    btn_rename.configure(bg=button_bg, fg=button_fg, activebackground=hover_bg,
                        activeforeground="white", relief=tk.FLAT, bd=0)
    btn_delete_table.configure(bg=delete_bg, fg="white", activebackground="#bb2d3b",
                              activeforeground="white", relief=tk.FLAT, bd=0)
    btn_clear_all.configure(bg="#ffc107", fg="#212529", activebackground="#ffcd39",
                           activeforeground="#212529", relief=tk.FLAT, bd=0)
    btn_toggle_mode.configure(bg="#6c757d", fg="white", activebackground="#5c636a",
                        activeforeground="white", relief=tk.FLAT, bd=0)
    btn_fullscreen.configure(bg="#28a745", fg="white", activebackground="#218838",
                             activeforeground="white", relief=tk.FLAT, bd=0)
    
    # Treeview style
    style = ttk.Style()
    style.theme_use('default')
    
    # Configure Treeview
    style.configure("Custom.Treeview",
                    background=even_bg,
                    foreground=fg_color,
                    fieldbackground=even_bg,
                    rowheight=30,
                    font=('Segoe UI', 10))
    
    style.configure("Custom.Treeview.Heading",
                    background=header_bg,
                    foreground=header_fg,
                    relief="flat",
                    font=('Segoe UI', 10, 'bold'))
    
    style.map("Custom.Treeview.Heading",
              background=[('active', '#dee2e6' if not dark_mode else '#4a4a5a')])
    
    style.map("Custom.Treeview",
              background=[('selected', '#0d6efd')],
              foreground=[('selected', 'white')])
    
    # Apply style to tree
    tree.configure(style="Custom.Treeview")
    
    # Configure row tags
    tree.tag_configure("even", background=even_bg, foreground=fg_color)
    tree.tag_configure("odd", background=odd_bg, foreground=fg_color)
    
    # Configure scrollbars
    style.configure("Vertical.TScrollbar", background=bg_color, troughcolor=bg_color)
    style.configure("Horizontal.TScrollbar", background=bg_color, troughcolor=bg_color)
    
    # Status bar
    status_bar.configure(bg=status_bg)
    status_label.configure(bg=status_bg, fg=fg_color)
    
    # Info label
    info_label.configure(bg=bg_color, fg="#ffc107" if dark_mode else "#856404")

def toggle_mode():
    global dark_mode
    dark_mode = not dark_mode
    apply_theme()

# =========================
# GUI
# =========================
root = tk.Tk()
root.title("🔍 Magic File Validator")
root.geometry("1300x700")
root.minsize(1000, 550)

# Set fullscreen
root.attributes("-fullscreen", True)

# Bind escape key to exit fullscreen
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
root.bind("<F11>", toggle_fullscreen)

# Main container
frame_main = tk.Frame(root)
frame_main.pack(fill=tk.BOTH, expand=True)

# ===== TITLE SECTION =====
title_frame = tk.Frame(frame_main, height=80)
title_frame.pack(fill=tk.X, padx=0, pady=0)
title_frame.pack_propagate(False)

title_label = tk.Label(title_frame, text="🔍 MAGIC FILE VALIDATOR", 
                       font=("Segoe UI", 20, "bold"))
title_label.pack(pady=(15, 5))

subtitle_label = tk.Label(title_frame, text="Deteksi & Validasi File Berdasarkan Magic Number (Support Semua Format File)", 
                          font=("Segoe UI", 11))
subtitle_label.pack()

# Separator line
separator = tk.Frame(frame_main, height=2, bg="#0d6efd")
separator.pack(fill=tk.X, padx=0, pady=5)

# ===== TABLE SECTION =====
columns = ("Nama File", "Ekstensi", "Hex Header (16 byte)", "Magic Number", "Tipe Asli", "Status")

# Frame for table
tree_frame = tk.Frame(frame_main)
tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

# Scrollbars
scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, style="Vertical.TScrollbar")
scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, style="Horizontal.TScrollbar")

# Treeview
tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                    yscrollcommand=scrollbar_y.set,
                    xscrollcommand=scrollbar_x.set,
                    height=20)

scrollbar_y.config(command=tree.yview)
scrollbar_x.config(command=tree.xview)

# Configure column widths and alignment
column_configs = {
    "Nama File": {"width": 350, "anchor": "w", "minwidth": 200},
    "Ekstensi": {"width": 100, "anchor": "center", "minwidth": 80},
    "Hex Header (16 byte)": {"width": 400, "anchor": "center", "minwidth": 300},
    "Magic Number": {"width": 200, "anchor": "center", "minwidth": 150},
    "Tipe Asli": {"width": 120, "anchor": "center", "minwidth": 100},
    "Status": {"width": 120, "anchor": "center", "minwidth": 100}
}

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, 
                width=column_configs[col]["width"],
                anchor=column_configs[col]["anchor"],
                minwidth=column_configs[col]["minwidth"])

# Grid layout
tree.grid(row=0, column=0, sticky="nsew")
scrollbar_y.grid(row=0, column=1, sticky="ns")
scrollbar_x.grid(row=1, column=0, sticky="ew")

tree_frame.grid_rowconfigure(0, weight=1)
tree_frame.grid_columnconfigure(0, weight=1)

# ===== CONTROL SECTION =====
control_frame = tk.Frame(frame_main)
control_frame.pack(pady=15, fill=tk.X, padx=20)

# Left side buttons
left_buttons = tk.Frame(control_frame)
left_buttons.pack(side=tk.LEFT)

btn_select = tk.Button(left_buttons, text="📁 Pilih File", command=select_files,
                       font=("Segoe UI", 10, "bold"), padx=20, pady=8, cursor="hand2")
btn_select.pack(side=tk.LEFT, padx=5)

# Extension input group
ext_frame = tk.Frame(control_frame)
ext_frame.pack(side=tk.LEFT, padx=15)

ext_label = tk.Label(ext_frame, text="Ekstensi Baru:", font=("Segoe UI", 10))
ext_label.pack(side=tk.LEFT, padx=5)

entry_ext = tk.Entry(ext_frame, width=12, font=("Segoe UI", 10, "bold"), 
                     justify="center", relief=tk.SOLID, bd=1)
entry_ext.pack(side=tk.LEFT, padx=5)
entry_ext.insert(0, "jpg")

btn_rename = tk.Button(ext_frame, text="✏️ Ubah Ekstensi", command=rename_files,
                       font=("Segoe UI", 10, "bold"), padx=20, pady=8, cursor="hand2")
btn_rename.pack(side=tk.LEFT, padx=5)

# Right side buttons
right_buttons = tk.Frame(control_frame)
right_buttons.pack(side=tk.RIGHT)

btn_delete_table = tk.Button(right_buttons, text="🗑️ Hapus dari Tampilan", command=delete_from_table_only,
                              font=("Segoe UI", 10, "bold"), padx=20, pady=8, cursor="hand2")
btn_delete_table.pack(side=tk.LEFT, padx=5)

btn_clear_all = tk.Button(right_buttons, text="🧹 Hapus Semua", command=clear_all_table,
                          font=("Segoe UI", 10, "bold"), padx=20, pady=8, cursor="hand2")
btn_clear_all.pack(side=tk.LEFT, padx=5)

btn_toggle_mode = tk.Button(right_buttons, text="🌙 Dark / ☀️ Light", command=toggle_mode,
                       font=("Segoe UI", 10, "bold"), padx=15, pady=8, cursor="hand2")
btn_toggle_mode.pack(side=tk.LEFT, padx=5)

btn_fullscreen = tk.Button(right_buttons, text="🖥️ Fullscreen", command=toggle_fullscreen,
                          font=("Segoe UI", 10, "bold"), padx=15, pady=8, cursor="hand2")
btn_fullscreen.pack(side=tk.LEFT, padx=5)

# Info label
info_frame = tk.Frame(frame_main)
info_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

info_label = tk.Label(info_frame, text="ℹ️  Support MP4 (ftyp, mp42, isom, mp41, msvn)  |  Tombol 'Hapus dari Tampilan' hanya menghapus dari daftar, file asli tetap aman  |  Tekan F11 atau ESC untuk mengatur layar penuh",
                      font=("Segoe UI", 9), anchor="center")
info_label.pack()

# Status bar
status_bar = tk.Frame(frame_main, height=30)
status_bar.pack(fill=tk.X, side=tk.BOTTOM)

status_label = tk.Label(status_bar, text="✅ Siap | Magic Number Checker | Support MP4 | Hapus hanya dari tampilan", 
                        font=("Segoe UI", 9, "italic"), anchor="w")
status_label.pack(fill=tk.X, padx=15, pady=5)

# Initialize theme
apply_theme()

# Print magic numbers for debugging
print("Magic Numbers MP4:", MAGIC_NUMBERS["mp4"])

root.mainloop()