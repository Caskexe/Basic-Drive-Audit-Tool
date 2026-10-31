#!/usr/bin/env python3
# Basic Drive Audit Tool (BDAT)
# Audits every hard drive on a Windows PC and shows size, usage, file and folder counts in a table.
# Author: CASK.exe - https://github.com/Caskexe
# Repository: https://github.com/Caskexe/Basic-Drive-Audit-Tool
# Licence: MIT (see the LICENSE file)
#
# Run instructions: python drive-audit.py (Windows 10, Python 3.8 or newer)
# Requirements: none. Uses only the Python standard library (tkinter, ctypes, os, shutil, csv).
# To build an exe, run build-exe.bat in this folder.

import csv
import ctypes
import os
import queue
import shutil
import string
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

APP_NAME = "Basic Drive Audit Tool"
APP_SHORT = "BDAT"
APP_AUTHOR = "CASK.exe"
AUTHOR_URL = "https://github.com/Caskexe"
REPO_URL = "https://github.com/Caskexe/Basic-Drive-Audit-Tool"
LICENCE_NAME = "MIT Licence"

# Windows drive type codes returned by GetDriveTypeW
DRIVE_REMOVABLE = 2
DRIVE_FIXED = 3
DRIVE_REMOTE = 4

# Attribute flag set on junctions and symbolic links
FILE_ATTRIBUTE_REPARSE_POINT = 0x400

# Column definitions: key, heading, width, alignment
COLUMNS = [
	("letter", "Drive Letter", 90, "center"),
	("name", "Drive Name", 180, "w"),
	("total", "Total Size", 110, "e"),
	("used", "Size Used", 110, "e"),
	("free", "Size Free", 110, "e"),
	("files", "File Count", 110, "e"),
	("folders", "Folder Count", 110, "e"),
	("both", "File and Folder Count", 150, "e"),
]

BLACK = "#000000"
WHITE = "#FFFFFF"
ROW_ALT = "#F2F2F2"
LINK_BLUE = "#0B5CAD"


def resource_path(name):
	# Find bundled files both when run as a script and when frozen into an exe
	base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
	return os.path.join(base, name)


def format_size(num_bytes):
	# Windows style sizes (1 GB is 1024 MB), so figures match File Explorer
	size = float(num_bytes)
	for unit in ("B", "KB", "MB", "GB", "TB"):
		if size < 1024 or unit == "TB":
			return f"{size:,.0f} {unit}" if unit == "B" else f"{size:,.2f} {unit}"
		size /= 1024


def get_drives(include_other):
	# Return a list of (letter, type) for the drives that exist on this machine
	kernel32 = ctypes.windll.kernel32
	bitmask = kernel32.GetLogicalDrives()
	drives = []
	for i, letter in enumerate(string.ascii_uppercase):
		if not bitmask & (1 << i):
			continue
		root = f"{letter}:\\"
		drive_type = kernel32.GetDriveTypeW(root)
		if drive_type == DRIVE_FIXED or (include_other and drive_type in (DRIVE_REMOVABLE, DRIVE_REMOTE)):
			drives.append((letter, drive_type))
	return drives


def get_volume_label(root):
	# Read the volume label, falling back to a generic name when none is set
	label_buf = ctypes.create_unicode_buffer(261)
	fs_buf = ctypes.create_unicode_buffer(261)
	ok = ctypes.windll.kernel32.GetVolumeInformationW(
		root, label_buf, 261, None, None, None, fs_buf, 261
	)
	if ok and label_buf.value:
		return label_buf.value
	return "Local Disk"


def is_reparse_point(entry):
	# Junctions and symlinks are skipped so folders are not counted twice or looped
	try:
		attrs = entry.stat(follow_symlinks=False).st_file_attributes
		return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
	except OSError:
		return True


def scan_drive(root, stop_event, progress_cb):
	# Walk the whole drive with an explicit stack and count files and folders
	files = 0
	folders = 0
	stack = [root]
	last_report = 0
	while stack:
		if stop_event.is_set():
			break
		current = stack.pop()
		try:
			with os.scandir(current) as it:
				for entry in it:
					try:
						if entry.is_dir(follow_symlinks=False):
							if is_reparse_point(entry):
								continue
							folders += 1
							stack.append(entry.path)
						elif entry.is_file(follow_symlinks=False):
							files += 1
					except OSError:
						continue
		except (PermissionError, FileNotFoundError, OSError):
			# Locked system folders are skipped quietly
			continue
		# Send a progress update every few thousand items to keep the UI moving
		if files + folders - last_report >= 5000:
			last_report = files + folders
			progress_cb(files, folders)
	return files, folders


class DriveAuditApp:
	def __init__(self, root):
		self.root = root
		self.root.title(f"{APP_NAME} ({APP_SHORT})")
		self.root.geometry("1050x440")
		self.root.minsize(900, 340)

		# Use the bundled icon when it is available
		try:
			self.root.iconbitmap(resource_path("drive-audit.ico"))
		except tk.TclError:
			pass

		self.queue = queue.Queue()
		self.stop_event = threading.Event()
		self.threads = []
		self.rows = {}
		self.pending = 0

		self.build_ui()
		self.poll_queue()

	def build_ui(self):
		# Table styling: black header row with centred white text
		style = ttk.Style()
		style.theme_use("clam")
		style.configure(
			"Treeview.Heading",
			background=BLACK,
			foreground=WHITE,
			font=("Segoe UI", 10, "bold"),
			relief="flat",
			anchor="center",
		)
		style.map("Treeview.Heading", background=[("active", BLACK)])
		style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)

		top = ttk.Frame(self.root, padding=10)
		top.pack(fill="x")

		self.scan_btn = ttk.Button(top, text="Scan Drives", command=self.start_scan)
		self.scan_btn.pack(side="left")
		self.stop_btn = ttk.Button(top, text="Stop", command=self.stop_scan, state="disabled")
		self.stop_btn.pack(side="left", padx=(6, 0))
		self.export_btn = ttk.Button(top, text="Export CSV", command=self.export_csv, state="disabled")
		self.export_btn.pack(side="left", padx=(6, 0))

		self.include_other = tk.BooleanVar(value=False)
		ttk.Checkbutton(
			top, text="Include removable and network drives", variable=self.include_other
		).pack(side="left", padx=(16, 0))

		ttk.Button(top, text="About", command=self.show_about).pack(side="right")

		# Table with a scrollbar
		frame = ttk.Frame(self.root, padding=(10, 0, 10, 0))
		frame.pack(fill="both", expand=True)

		self.tree = ttk.Treeview(frame, columns=[c[0] for c in COLUMNS], show="headings", selectmode="browse")
		for key, heading, width, anchor in COLUMNS:
			self.tree.heading(key, text=heading, anchor="center")
			self.tree.column(key, width=width, anchor=anchor, stretch=True)
		self.tree.tag_configure("alt", background=ROW_ALT)
		scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
		self.tree.configure(yscrollcommand=scroll.set)
		self.tree.pack(side="left", fill="both", expand=True)
		scroll.pack(side="right", fill="y")

		# Footer with the status message on the left and the credit link on the right
		footer = ttk.Frame(self.root, padding=(10, 8))
		footer.pack(fill="x")
		self.status = tk.StringVar(value="Ready. Click Scan Drives to begin.")
		ttk.Label(footer, textvariable=self.status).pack(side="left")
		credit = tk.Label(
			footer, text=f"Made by {APP_AUTHOR}", fg=LINK_BLUE, cursor="hand2",
			font=("Segoe UI", 9, "underline"),
		)
		credit.pack(side="right")
		credit.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_URL))

	def show_about(self):
		# Small About window with the credit, repository link and licence
		win = tk.Toplevel(self.root)
		win.title(f"About {APP_SHORT}")
		win.resizable(False, False)
		win.transient(self.root)
		try:
			win.iconbitmap(resource_path("drive-audit.ico"))
		except tk.TclError:
			pass

		body = ttk.Frame(win, padding=20)
		body.pack()
		ttk.Label(body, text=f"{APP_NAME} ({APP_SHORT})", font=("Segoe UI", 13, "bold")).pack(anchor="w")
		ttk.Label(body, text="Audits every hard drive and lists size, usage, file and folder counts.").pack(anchor="w", pady=(6, 12))
		ttk.Label(body, text=f"Created by {APP_AUTHOR}").pack(anchor="w")

		def link(text, url):
			lbl = tk.Label(body, text=text, fg=LINK_BLUE, cursor="hand2", font=("Segoe UI", 9, "underline"))
			lbl.pack(anchor="w")
			lbl.bind("<Button-1>", lambda e: webbrowser.open(url))

		link(AUTHOR_URL, AUTHOR_URL)
		ttk.Label(body, text="Source code:").pack(anchor="w", pady=(10, 0))
		link(REPO_URL, REPO_URL)
		ttk.Label(body, text=f"Open source under the {LICENCE_NAME}.").pack(anchor="w", pady=(10, 0))
		ttk.Button(body, text="Close", command=win.destroy).pack(anchor="e", pady=(14, 0))

	def start_scan(self):
		# Clear old results and start one worker thread per drive
		self.stop_event.clear()
		self.tree.delete(*self.tree.get_children())
		self.rows.clear()
		self.threads.clear()

		drives = get_drives(self.include_other.get())
		if not drives:
			messagebox.showinfo(APP_SHORT, "No drives were found.")
			return

		self.pending = len(drives)
		self.scan_btn.config(state="disabled")
		self.stop_btn.config(state="normal")
		self.export_btn.config(state="disabled")
		self.status.set(f"Scanning {len(drives)} drive(s). Large drives can take several minutes.")

		for index, (letter, _) in enumerate(drives):
			root_path = f"{letter}:\\"
			# Fill in the quick details first so the row appears straight away
			try:
				usage = shutil.disk_usage(root_path)
				total, used, free = usage.total, usage.used, usage.free
			except OSError:
				total = used = free = 0
			tags = ("alt",) if index % 2 else ()
			iid = self.tree.insert("", "end", tags=tags, values=(
				f"{letter}:",
				get_volume_label(root_path),
				format_size(total),
				format_size(used),
				format_size(free),
				"Scanning...", "Scanning...", "Scanning...",
			))
			self.rows[letter] = iid
			t = threading.Thread(target=self.worker, args=(letter, root_path), daemon=True)
			self.threads.append(t)
			t.start()

	def worker(self, letter, root_path):
		# Runs in a background thread and reports through the queue
		def progress(files, folders):
			self.queue.put(("progress", letter, files, folders))
		files, folders = scan_drive(root_path, self.stop_event, progress)
		self.queue.put(("done", letter, files, folders))

	def stop_scan(self):
		self.stop_event.set()
		self.status.set("Stopping. Counts for unfinished drives will be partial.")

	def set_counts(self, letter, files, folders, final):
		iid = self.rows.get(letter)
		if not iid:
			return
		suffix = "" if final else "+"
		self.tree.set(iid, "files", f"{files:,}{suffix}")
		self.tree.set(iid, "folders", f"{folders:,}{suffix}")
		self.tree.set(iid, "both", f"{files + folders:,}{suffix}")

	def poll_queue(self):
		# Pull any waiting messages from the workers and update the table
		try:
			while True:
				kind, letter, files, folders = self.queue.get_nowait()
				if kind == "progress":
					self.set_counts(letter, files, folders, final=False)
				else:
					self.set_counts(letter, files, folders, final=True)
					self.pending -= 1
					if self.pending <= 0:
						self.finish_scan()
		except queue.Empty:
			pass
		self.root.after(100, self.poll_queue)

	def finish_scan(self):
		self.scan_btn.config(state="normal")
		self.stop_btn.config(state="disabled")
		self.export_btn.config(state="normal")
		self.status.set("Scan stopped early." if self.stop_event.is_set() else "Scan complete.")

	def export_csv(self):
		# Save the table as a CSV file
		path = filedialog.asksaveasfilename(
			defaultextension=".csv",
			filetypes=[("CSV files", "*.csv")],
			initialfile="bdat-drive-audit.csv",
		)
		if not path:
			return
		with open(path, "w", newline="", encoding="utf-8-sig") as f:
			writer = csv.writer(f)
			writer.writerow([c[1] for c in COLUMNS])
			for iid in self.tree.get_children():
				writer.writerow(self.tree.item(iid, "values"))
		self.status.set(f"Exported to {path}")


def main():
	if os.name != "nt":
		print(f"{APP_NAME} is built for Windows.")
		return
	root = tk.Tk()
	DriveAuditApp(root)
	root.mainloop()


if __name__ == "__main__":
	main()
