import os
import requests 
import time
import threading
from colorama import Fore, init 
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import ctypes

init(autoreset=True)

class colors:
    CRED2 = Fore.RED
    CBLUE2 = Fore.BLUE
    OKGREEN = Fore.GREEN

lock = threading.Lock()
REQUEST_DELAY = 5  # seconds
MAX_WORKERS = 40  # Maximum number of concurrent workers
VALIDATION_URL = 'https://checkeremail.com/checker-validation.php'  # Validation URL

def get_payload(email):
    domain = email.split('@')[1]
    payload = {'em': email, 'ch': '2m14racqo107o0p0725b', 'hl': 'checkeremail.com', 'frm': 'example@gmail.com'}
    
    if 'gmail' in domain:
        payload['hl'] = 'checkeremail.com'
        payload['frm'] = 'example@gmail.com'
    elif 'yahoo' in domain:
        payload['hl'] = 'checkeryahoo.com'
        payload['frm'] = 'example@yahoo.com'
    elif 'hotmail' in domain or 'outlook' in domain:
        payload['hl'] = 'checkerhotmail.com'
        payload['frm'] = 'example@hotmail.com'
    else:
        return None  # Return None if the domain is not Yahoo, Hotmail, or Gmail
    
    return payload

def work(email, progress_counter, total_emails, fileOpen, fileOpenCheck, fileOpenIn, headers):
    payload = get_payload(email)
    if not payload:
        with lock:
            progress_counter[2] += 1
            print(colors.CRED2 + '[~] Invalid ' + colors.CBLUE2 + email + colors.CRED2 + " ====> [Not a supported domain]\n", end='')
            with open(fileOpenCheck, 'a') as invalid:
                invalid.write(email + '\n')
        return

    time.sleep(REQUEST_DELAY)  # Simulate delay

    try:
        checkeremail = requests.post(VALIDATION_URL, headers=headers, data=payload)
        checkeremail.raise_for_status()  # Raise an error for bad HTTP status codes
    except requests.RequestException as e:
        print(colors.CRED2 + f"Error validating {email}: {e}")
        return

    response = checkeremail.content.decode('utf-8')
    with lock:
        if 'Address is valid' in response:
            print(colors.OKGREEN + '[+] Valid ' + colors.CBLUE2 + email + colors.OKGREEN + ' ====> [Live.]\n', end='')
            with open(fileOpen, 'a') as valid:
                valid.write(email + '\n')
            progress_counter[0] += 1
        elif 'The address can not receive mail' in response:
            print(colors.CRED2 + '[~] Dead ' + colors.CBLUE2 + email + colors.CRED2 + " ====> [Can't receive mail]\n", end='')
            with open(fileOpenIn, 'a') as invalid:
                invalid.write(email + '\n')
            progress_counter[1] += 1
        else:
            print(colors.CRED2 + '[~] Invalid ' + colors.CBLUE2 + email + colors.CRED2 + " ====> [Can't verify]\n", end='')
            with open(fileOpenCheck, 'a') as invalid:
                invalid.write(email + '\n')
            progress_counter[2] += 1

        if os.name == 'nt':
            ctypes.windll.kernel32.SetConsoleTitleW(
                f'Email Validator Tool - Valid[{progress_counter[0]}] '
                f'Dead[{progress_counter[1]}] '
                f'Invalid[{progress_counter[2]}] '
                f'Processing: {progress_counter[0] + progress_counter[1] + progress_counter[2]}/{total_emails}'
            )

def main():
    check_emails = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.16; rv:86.0) Gecko/20100101 Firefox/86.0'
    }
    results_directory = os.path.join('Results')
    
    if not os.path.exists(results_directory):
        os.makedirs(results_directory)

    fileOpen = os.path.join(results_directory, 'Valid_emails.txt')
    fileOpenIn = os.path.join(results_directory, 'Invalid_emails.txt')
    fileOpenCheck = os.path.join(results_directory, 'Dead_emails.txt')

    if os.name == 'nt':
        ctypes.windll.kernel32.SetConsoleTitleW('Email Validator Tool - Initializing...')
    
    opFile = input(colors.CBLUE2 + 'Enter the filename containing the emails to check: ')
    print("")

    try:
        with open(opFile) as f:
            emails = [email.strip() for email in f]
    except FileNotFoundError:
        print(colors.CRED2 + "File not found. Please check the filename and try again.")
        return

    # Filter only Yahoo, Hotmail, and Gmail emails
    for email in emails:
        domain = email.split('@')[1].lower()
        if domain in ['yahoo.com', 'gmail.com', 'hotmail.com', 'outlook.com']:
            check_emails.append(email)

    if not check_emails:
        print(colors.CRED2 + "No valid emails found in the provided file.")
        return
    
    progress_counter = [0, 0, 0]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(work, email, progress_counter, len(check_emails), fileOpen, fileOpenCheck, fileOpenIn, headers) for email in check_emails]
        for future in futures:
            future.result()

    print(colors.OKGREEN + '\nValidation is done!')
    input('Press Enter to exit...')
    print(colors.OKGREEN + 'Exiting program. Goodbye!')
    time.sleep(3)

if __name__ == '__main__':
    main()
