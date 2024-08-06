#!/usr/bin/env python3

import subprocess
import sys

# List of required packages
required_packages = ['requests', 'tk']

# Function to install packages
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Check and install packages
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install(package)

# Importing the packages after ensuring they are installed
import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import re
import os

# Your existing code goes here


# Replace with your osu! client ID and client secret
CREDENTIALS_FILE = 'credentials.txt'

def save_credentials(client_id, client_secret):
    with open(CREDENTIALS_FILE, 'w') as file:
        file.write(f"{client_id}\n{client_secret}")

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as file:
            client_id = file.readline().strip()
            client_secret = file.readline().strip()
            return client_id, client_secret
    return None, None

def ask_credentials():
    popup = tk.Toplevel(root)
    popup.title("Enter Credentials")
    
    tk.Label(popup, text="Client ID:").grid(row=0, column=0, padx=10, pady=10)
    client_id_entry = tk.Entry(popup, width=50)
    client_id_entry.grid(row=0, column=1, padx=10, pady=10)
    
    tk.Label(popup, text="Client Secret:").grid(row=1, column=0, padx=10, pady=10)
    client_secret_entry = tk.Entry(popup, width=50, show="*")
    client_secret_entry.grid(row=1, column=1, padx=10, pady=10)
    
    def on_submit():
        global client_id, client_secret
        client_id = client_id_entry.get()
        client_secret = client_secret_entry.get()
        if client_id and client_secret:
            save_credentials(client_id, client_secret)
            popup.destroy()
        else:
            messagebox.showwarning("Input Error", "Please enter both Client ID and Client Secret.")

    submit_button = tk.Button(popup, text="Submit", command=on_submit)
    submit_button.grid(row=2, columnspan=2, pady=10)

    popup.grab_set()
    popup.wait_window()

def initial_setup():
    global client_id, client_secret
    client_id, client_secret = load_credentials()
    if not client_id or not client_secret:
        ask_credentials()
    return client_id, client_secret

def get_access_token(client_id, client_secret):
    token_url = 'https://osu.ppy.sh/oauth/token'
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
        'scope': 'public'
    }
    token_response = requests.post(token_url, data=token_data)
    token_response.raise_for_status()
    token = token_response.json().get('access_token')
    return token

def get_beatmap_data(beatmapset_id, token):
    beatmap_url = f'https://osu.ppy.sh/api/v2/beatmapsets/{beatmapset_id}'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(beatmap_url, headers=headers)
    response.raise_for_status()
    return response.json()

def extract_beatmapset_id(url):
    match = re.search(r'/beatmapsets/(\d+)', url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Invalid beatmap URL")

def get_creator_info(user_id, token):
    user_url = f'https://osu.ppy.sh/api/v2/users/{user_id}'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(user_url, headers=headers)
    response.raise_for_status()
    user_data = response.json()
    return user_data['username'], user_data['id']

def get_user_id_from_username(username, token):
    user_url = f'https://osu.ppy.sh/api/v2/users/{username}/osu'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(user_url, headers=headers)
    response.raise_for_status()
    user_data = response.json()
    return user_data['id']

def get_difficulty_info(beatmap_id, token):
    beatmap_url = f'https://osu.ppy.sh/api/v2/beatmaps/{beatmap_id}'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    response = requests.get(beatmap_url, headers=headers)
    response.raise_for_status()
    beatmap_data = response.json()
    return beatmap_data['version'], beatmap_data['difficulty_rating']

def map_difficulty_name_based_on_rating(star_rating):
    if star_rating < 2.0:
        return 'Easy'
    elif 2.0 <= star_rating < 2.7:
        return 'Normal'
    elif 2.7 <= star_rating < 4.0:
        return 'Hard'
    elif 4.0 <= star_rating < 5.3:
        return 'Insane'
    elif 5.3 <= star_rating < 6.5:
        return 'Expert'
    else:
        return 'Expert+'

def format_as_bbcode(original_name, core_difficulty_name, username, user_id):
    info = difficulty_info.get(core_difficulty_name)
    if not info:
        raise ValueError("Difficulty information is missing")
    return f"[img]{info['url']}[/img] [color={info['color']}] {original_name}[/color] - by [url=https://osu.ppy.sh/u/{user_id}]{username}[/url]"

def generate_bbcode():
    try:
        beatmap_url = url_entry.get()
        hitsounder = hitsounder_entry.get()
        beatmapset_id = extract_beatmapset_id(beatmap_url)
        token = get_access_token(client_id, client_secret)
        beatmap_data = get_beatmap_data(beatmapset_id, token)
        
        hitsounder_id = get_user_id_from_username(hitsounder, token)
        
        results = []
        for beatmap in beatmap_data['beatmaps']:
            beatmap_id = beatmap['id']
            user_id = beatmap['user_id']
            difficulty_name, star_rating = get_difficulty_info(beatmap_id, token)
            
            core_difficulty_name = map_difficulty_name_based_on_rating(star_rating)
            if core_difficulty_name is None:
                results.append(f"Difficulty '{difficulty_name}' is not recognized.")
                continue
            
            username, _ = get_creator_info(user_id, token)
            results.append((star_rating, difficulty_name, core_difficulty_name, username))
        
        results.sort(key=lambda x: x[0])
        
        bbcode_results = [
            format_as_bbcode(difficulty_name, core_difficulty_name, username, user_id)
            for _, difficulty_name, core_difficulty_name, username in results
        ]
        
        bbcode_results.append(f"\nHitsounds by [url=https://osu.ppy.sh/u/{hitsounder_id}]{hitsounder}[/url]")
        
        final_text = "[centre][size=150]\n" + "\n".join(bbcode_results) + "\n[/size][/centre]"
        
        update_display(final_text)
        
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_display(text):
    result_display.config(state=tk.NORMAL)
    result_display.delete(1.0, tk.END)
    result_display.insert(tk.END, text)
    result_display.config(state=tk.DISABLED)

def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(result_display.get(1.0, tk.END).strip())
    messagebox.showinfo("Copied", "BBCode copied to clipboard!")

def edit_credentials():
    ask_credentials()
    global client_id, client_secret
    client_id, client_secret = load_credentials()

# Create the main window
root = tk.Tk()
root.title("Beatmap BBCode Generator")

# Initialize client ID and client secret
client_id, client_secret = initial_setup()

difficulty_info = {
    'Easy': {'url': 'https://i.ppy.sh/e4046437c0d195a3f2bed4b4140a41d696bdf7f0/68747470733a2f2f6f73752e7070792e73682f77696b692f696d616765732f7368617265642f646966662f656173792d6f2e706e673f3230323131323135', 'color': '#8cccec'},
    'Normal': {'url': 'https://i.ppy.sh/20d7052354c61f8faf3a4828d9ff7751bb6776b1/68747470733a2f2f6f73752e7070792e73682f77696b692f696d616765732f7368617265642f646966662f6e6f726d616c2d6f2e706e673f3230323131323135', 'color': '#68fc94'},
    'Hard': {'url': 'https://i.ppy.sh/0ad2e280f5a26c7f202b3dff711b723045662b37/68747470733a2f2f6f73752e7070792e73682f77696b692f696d616765732f7368617265642f646966662f686172642d6f2e706e673f3230323131323135', 'color': '#f8ec5c'},
    'Insane': {'url': 'https://i.ppy.sh/f6eabcfbacdfe85e520106702ec3a382a0430d40/68747470733a2f2f6f73752e7070792e73682f77696b692f696d616765732f7368617265642f646966662f696e73616e652d6f2e706e673f3230323131323135', 'color': '#ff7c6c'},
    'Expert': {'url': 'https://i.ppy.sh/3b561ef8a73118940b59e79f3433bfa98c26cbf1/68747470733a2f2f6f73752e7070792e73682f77696b692f696d616765732f7368617265642f646966662f657870657274706c75732d6f2e706e673f3230323131323135', 'color': '#8000FF'},
    'Expert+': {'url': 'https://i.ppy.sh/3b561ef8a73118940b59e79f3433bfa98c26cbf1/68747470733a2f2f6f73752e7070792e73682f77696b692f696d616765732f7368617265642f646966662f657870657274706c75732d6f2e706e673f3230323131323135', 'color': '#8000FF'}
}

# URL input
tk.Label(root, text="Enter beatmap URL:").pack(pady=5)
url_entry = tk.Entry(root, width=80)
url_entry.pack(pady=5)

# Hitsounder input
tk.Label(root, text="Enter hitsounder username or ID:").pack(pady=5)
hitsounder_entry = tk.Entry(root, width=80)
hitsounder_entry.pack(pady=5)

# Edit Credentials button
edit_button = tk.Button(root, text="Edit Credentials", command=edit_credentials)
edit_button.pack(pady=10)

# Submit button
submit_button = tk.Button(root, text="Generate BBCode", command=generate_bbcode)
submit_button.pack(pady=10)

# Result display area
result_display = scrolledtext.ScrolledText(root, width=80, height=20)
result_display.pack(pady=10)
result_display.config(state=tk.DISABLED)

# Copy to Clipboard button (moved under the text box)
copy_button = tk.Button(root, text="Copy to Clipboard", command=copy_to_clipboard)
copy_button.pack(pady=5)

# Run the application
root.mainloop()
