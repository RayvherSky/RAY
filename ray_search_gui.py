import tkinter as tk
from tkinter import ttk
import subprocess
import os
import threading

ES_PATH = "es.exe"  # or full path

def everything_search(query, max_results=100):
    """Return list of full paths from Everything."""
    if not query.strip():
        return []
    try:
        result = subprocess.run(
            [ES_PATH, "-full-path-and-name", "-limit", str(max_results), query],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0 and result.stdout:
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return []
    except Exception:
        return []

class EverythingSearchGUI:
    def __init__(self, root):
        self.root = root
        root.title("RAY Search - Everything")
        root.geometry("800x500")
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_change)
        self.entry = ttk.Entry(root, textvariable=self.search_var, font=("Arial", 12))
        self.entry.pack(fill=tk.X, padx=10, pady=10)
        self.entry.focus()
        
        # Listbox with scrollbar
        frame = ttk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, font=("Consolas", 10))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Bind double-click to open
        self.listbox.bind("<Double-Button-1>", self.open_selected)
        self.listbox.bind("<Return>", self.open_selected)
        
        # Status label
        self.status = ttk.Label(root, text="Type to search...", foreground="gray")
        self.status.pack(pady=5)
        
        self.current_results = []  # store full paths
    
    def on_search_change(self, *args):
        query = self.search_var.get()
        if len(query) < 2:
            self.listbox.delete(0, tk.END)
            self.status.config(text="Type at least 2 characters")
            return
        
        self.status.config(text=f"Searching for '{query}'...")
        # Run search in background so GUI doesn't freeze
        threading.Thread(target=self.do_search, args=(query,), daemon=True).start()
    
    def do_search(self, query):
        results = everything_search(query)
        self.root.after(0, self.update_results, results)
    
    def update_results(self, results):
        self.listbox.delete(0, tk.END)
        self.current_results = results
        for path in results:
            # Show only filename/foldername, but store full path
            name = os.path.basename(path) if os.path.sep in path else path
            # Add folder indicator
            if os.path.isdir(path):
                display = f"📁 {name}  ({path})"
            else:
                display = f"📄 {name}  ({path})"
            self.listbox.insert(tk.END, display)
        self.status.config(text=f"Found {len(results)} items")
    
    def open_selected(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        full_path = self.current_results[idx]
        try:
            os.startfile(full_path)
            self.status.config(text=f"Opened: {full_path}")
        except Exception as e:
            self.status.config(text=f"Error: {e}")

def launch_search_window():
    root = tk.Tk()
    app = EverythingSearchGUI(root)
    root.mainloop()

if __name__ == "__main__":
    launch_search_window()