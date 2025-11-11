import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from tkinterdnd2 import DND_FILES, TkinterDnD
import requests
import base64
import threading
import urllib.parse
import re

# =======================
# 환경변수에서 토큰과 사용자 이름 불러오기
# =======================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USER = os.getenv("GITHUB_USER")

if not GITHUB_TOKEN or not GITHUB_USER:
    raise ValueError("환경변수 GITHUB_TOKEN 또는 GITHUB_USER가 설정되지 않았습니다.")

# =======================
# GitHub API 관련
# =======================
def get_repos(filter_option="all"):
    url = "https://api.github.com/user/repos?per_page=100"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        repos = resp.json()
        if filter_option == "public":
            return [repo['name'] for repo in repos if not repo['private']]
        elif filter_option == "private":
            return [repo['name'] for repo in repos if repo['private']]
        else:
            return [repo['name'] for repo in repos]
    else:
        messagebox.showerror("Error", f"Failed to fetch repos: {resp.status_code}")
        return []

def is_private_repo(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json().get("private", False)
    return False

def encode_github_path(path):
    return "/".join([urllib.parse.quote(p, safe='') for p in path.split("/")])

def get_github_contents(repo_name, path=""):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/{encode_github_path(path)}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return []

def make_unique_name(repo_name, path):
    path = path.replace("\\", "/")
    base, ext = os.path.splitext(path)
    counter = 1
    new_path = path
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    while True:
        url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/{encode_github_path(new_path)}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 404:
            break
        counter += 1
        new_path = f"{base}_{counter}{ext}"
    return new_path

def create_github_folder(repo_name, folder_path):
    if not folder_path:
        return False
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/{encode_github_path(folder_path)}/.gitkeep"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = {"message": f"Create folder {folder_path}", "content": ""}
    resp = requests.put(url, headers=headers, json=data)
    return resp.status_code in [200, 201]

def ensure_github_folder(repo_name, folder_path):
    if not folder_path:
        return
    items = get_github_contents(repo_name, folder_path)
    if not items:
        create_github_folder(repo_name, folder_path)

# =======================
# 파일 업로드
# =======================
def get_relative_path(file_path, base_path=None):
    try:
        if base_path:
            return os.path.relpath(file_path, base_path)
        else:
            return os.path.basename(file_path)
    except ValueError:
        return os.path.basename(file_path)

def upload_file(repo_name, file_path, github_root="", local_base_path=None,
                progress_label=None, progress_bar=None, index=None, total=None, stop_event=None):
    if stop_event and stop_event.is_set():
        return
    rel_path_local = get_relative_path(file_path, local_base_path)
    rel_path = os.path.join(github_root, rel_path_local).replace("\\", "/") if github_root else rel_path_local.replace("\\", "/")
    folder_only = os.path.dirname(rel_path)
    if folder_only:
        ensure_github_folder(repo_name, folder_only)
    rel_path_unique = make_unique_name(repo_name, rel_path)
    url = f"https://api.github.com/repos/{GITHUB_USER}/{repo_name}/contents/{encode_github_path(rel_path_unique)}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    data = {"message": f"Add {rel_path_unique}", "content": content}
    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code not in [200, 201]:
        print(f"Failed: {rel_path_unique} ({resp.status_code})")
    if progress_label and index is not None and total is not None:
        progress_label.after(0, lambda: progress_label.config(text=f"Uploading: {rel_path_unique} ({index}/{total})"))
    if progress_bar and index is not None and total is not None:
        progress_bar.after(0, lambda: progress_bar.config(value=(index / total) * 100))

def upload_folder(repo_name, folder_path, github_root="", progress_label=None, progress_bar=None, stop_event=None, start_index=1, local_base_path=None):
    files_list = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            files_list.append(os.path.join(root, file))
    total_files = len(files_list)
    local_base = local_base_path if local_base_path else os.path.dirname(folder_path)
    for idx, file_path in enumerate(files_list, start=start_index):
        if stop_event and stop_event.is_set():
            break
        upload_file(repo_name, file_path, github_root=github_root, local_base_path=local_base,
                    progress_label=progress_label, progress_bar=progress_bar, index=idx, total=total_files+start_index-1,
                    stop_event=stop_event)
    return total_files

# =======================
# GUI
# =======================
class GitHubDnDUploader(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("GitHub Drag & Drop Backup")
        self.geometry("600x850")
        self.stop_event = None
        self.upload_thread = None

        tk.Label(self, text="Select GitHub Repo:").pack()
        self.repo_listbox = tk.Listbox(self)
        self.repo_listbox.pack(fill=tk.BOTH, expand=False)
        self.repo_listbox.bind("<<ListboxSelect>>", self.refresh_tree)
        self.refresh_repo_list()

        frame = tk.Frame(self)
        frame.pack(fill=tk.X)
        tk.Label(frame, text="Select GitHub Folder/File (or leave empty for root):").pack(side=tk.LEFT)
        tk.Button(frame, text="New Folder", command=self.new_folder).pack(side=tk.RIGHT)

        self.tree = ttk.Treeview(self)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.heading("#0", text="GitHub Folders & Files")
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_open)

        self.progress_label = tk.Label(self, text="", fg="blue")
        self.progress_label.pack(pady=5)
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=550, mode="determinate")
        self.progress_bar.pack(pady=5)
        self.cancel_button = tk.Button(self, text="Cancel Upload", command=self.cancel_upload)
        self.cancel_button.pack(pady=5)

        tk.Label(self, text="Drag & Drop files or folders here:").pack(pady=5)
        self.drop_area = tk.Label(self, text="Drop files/folders here", bg="lightgray", height=14)
        self.drop_area.pack(fill=tk.BOTH, padx=10, pady=10)
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.handle_drop)

    # =======================
    # GUI 함수
    # =======================
    def refresh_repo_list(self):
        self.repo_listbox.delete(0, tk.END)
        repos = get_repos()
        for repo in repos:
            self.repo_listbox.insert(tk.END, repo)

    def refresh_tree(self, event=None):
        self.tree.delete(*self.tree.get_children())
        root_node = self.tree.insert("", "end", text="메인(루트)", values=("", "dir"))
        self.add_dummy_children(root_node)

    def add_dummy_children(self, node):
        self.tree.insert(node, "end", text="dummy")

    def on_tree_open(self, event):
        node = self.tree.focus()
        children = self.tree.get_children(node)
        if children and self.tree.item(children[0], "text") == "dummy":
            self.tree.delete(children[0])
            path = self.tree.item(node, "values")[0]
            selection = self.repo_listbox.curselection()
            if selection:
                repo_name = self.repo_listbox.get(selection[0])
                self.build_tree(node, repo_name, path)

    def build_tree(self, parent, repo_name, path=""):
        items = get_github_contents(repo_name, path)
        for item in items:
            if item["type"] == "dir":
                node = self.tree.insert(parent, "end", text=item["name"], values=(item["path"], item["type"]))
                self.add_dummy_children(node)
            else:
                self.tree.insert(parent, "end", text=item["name"], values=(item["path"], item["type"]))

    def new_folder(self):
        repo_selection = self.repo_listbox.curselection()
        if not repo_selection:
            messagebox.showwarning("Warning", "Select a repository first!")
            return
        repo_name = self.repo_listbox.get(repo_selection[0])
        sel = self.tree.selection()
        parent_path = self.tree.item(sel[0], "values")[0] if sel else ""
        folder_name = simpledialog.askstring("New Folder", "Enter new folder name:")
        if not folder_name:
            return
        new_path = os.path.join(parent_path, folder_name).replace("\\", "/")
        if create_github_folder(repo_name, new_path):
            self.refresh_tree()
            messagebox.showinfo("Success", f"Folder '{new_path}' created successfully!")

    def cancel_upload(self):
        if self.stop_event:
            self.stop_event.set()
            self.progress_label.config(text="Upload Cancelled")
            messagebox.showinfo("Cancelled", "Upload has been cancelled.")

    # ===== 공백 있는 파일/폴더 처리 =====
    def split_drop_paths(self, data):
        # 중괄호 안 경로 또는 공백 없는 경로 모두 추출
        pattern = r'\{([^}]+)\}|([^\s]+)'
        matches = re.findall(pattern, data)
        paths = [m[0] if m[0] else m[1] for m in matches]
        return paths

    def handle_drop(self, event):
        repo_selection = self.repo_listbox.curselection()
        if not repo_selection:
            messagebox.showwarning("Warning", "Select a repository first!")
            return
        repo_name = self.repo_listbox.get(repo_selection[0])
        sel = self.tree.selection()
        github_root = self.tree.item(sel[0], "values")[0] if sel else ""

        if is_private_repo(repo_name):
            proceed = messagebox.askyesno(
                "Private Repo Warning",
                f"'{repo_name}' is a private repository.\nAre you sure you want to upload?"
            )
            if not proceed:
                return

        raw_data = event.data
        paths = self.split_drop_paths(raw_data)

        files_to_upload, folders_to_upload = [], []
        for path in paths:
            path = os.path.normpath(path)
            if os.path.isfile(path):
                files_to_upload.append(path)
            elif os.path.isdir(path):
                folders_to_upload.append(path)

        if not files_to_upload and not folders_to_upload:
            messagebox.showwarning("Warning", "No valid files or folders detected!")
            return

        self.stop_event = threading.Event()
        self.upload_thread = threading.Thread(
            target=self.upload_paths,
            args=(repo_name, files_to_upload, folders_to_upload, github_root)
        )
        self.upload_thread.start()

    def upload_paths(self, repo_name, files, folders, github_root):
        current_index = 0
        total_files = len(files)
        for idx, file_path in enumerate(files, start=1):
            if self.stop_event.is_set():
                break
            upload_file(repo_name, file_path, github_root, local_base_path=None,
                        progress_label=self.progress_label, progress_bar=self.progress_bar,
                        index=idx, total=total_files, stop_event=self.stop_event)
            current_index += 1

        for folder_path in folders:
            if self.stop_event.is_set():
                break
            uploaded_count = upload_folder(repo_name, folder_path, github_root,
                                           progress_label=self.progress_label, progress_bar=self.progress_bar,
                                           stop_event=self.stop_event, start_index=current_index+1,
                                           local_base_path=None)
            current_index += uploaded_count

        if not self.stop_event.is_set():
            self.refresh_tree()
            self.progress_label.config(text="Upload Complete")
            self.progress_bar['value'] = 100
            messagebox.showinfo("Upload Complete", "Files/folders uploaded successfully!")

# =======================
# 실행
# =======================
if __name__ == "__main__":
    app = GitHubDnDUploader()
    app.mainloop()
