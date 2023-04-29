import itertools
import PyPDF2
import concurrent.futures
import re
import sys
import os
import random

# Define the character set and number set
char_set = 'QUTAILNMRY'
num_set = '0129'

def check_password(password, attempt_num):
    try:
        with open('encrypted.pdf', 'rb') as pdf_file:
            pdfReader = PyPDF2.PdfReader(pdf_file)
            if pdfReader.decrypt(password) == 1:
                print(f'Password found in attempt {attempt_num}: {password}')
                return True
            else:
                sys.stdout.write(f'\rAttempt {attempt_num}: {password}')
                sys.stdout.flush()
                return False
    except Exception as e:
        print(f'Error occurred in attempt {attempt_num} with password {password}: {e}')
        return False

def generate_passwords():
    """Generate all possible passwords that match the regex."""
    passwords = []
    for i in range(1, 5):
        char_combos = itertools.product(char_set, repeat=i)
        for char_combo in char_combos:
            num_combos = itertools.product(num_set, repeat=4)
            for num_combo in num_combos:
                password = ''.join(char_combo) + ''.join(num_combo)
                if re.match('^[A-Z]{1,4}[0-9]{4}$', password):
                    passwords.append(password)
    random.shuffle(passwords)
    return passwords

if __name__ == '__main__':

    if not os.path.exists('passwords.txt'):
        with open('passwords.txt', 'w'):
            pass

    # Load previously tried passwords
    tried_passwords = set()
    with open('passwords.txt', 'r') as f:
        for line in f:
            tried_passwords.add(line.strip())

    # Brute force attack with parallelism
    attempt_num = len(tried_passwords)
    found_password = None
    with concurrent.futures.ProcessPoolExecutor(max_workers=None) as executor:
        futures = {executor.submit(check_password, password, attempt_num + i + 1): password for i, password in enumerate(generate_passwords()) if password not in tried_passwords}
        for future in concurrent.futures.as_completed(futures):
            password = futures[future]
            if future.result():
                found_password = password
                break
            else:
                with open('passwords.txt', 'a') as f:
                    f.write(f'{password}\n')

    if found_password is not None:
        print(f'\nPassword found in attempt {attempt_num}: {found_password}')
    else:
        print(f'\nAll possible passwords tried, giving up')
