import itertools
import PyPDF2
import concurrent.futures
import re
import sys
import os
import random
import time
from tqdm import tqdm
from colorama import Fore, Style, init

def clear_terminal():
    print('\033[2J\033[H', end='')


def print_banner():
    banner = f'''
{Fore.CYAN}========================================
           PDF Password Cracker
========================================{Style.RESET_ALL}
'''
    print(banner)


def sanitize_input(prompt, pattern, error_msg):
    while True:
        user_input = input(prompt)
        if re.match(pattern, user_input):
            return user_input
        else:
            print(error_msg)


def get_user_inputs():
    clear_terminal()
    print_banner()

    char_set = sanitize_input("Enter the character set (uppercase letters only): ",
                              "^[A-Z]+$", "Invalid input. Please enter uppercase letters only.")
    num_set = sanitize_input("Enter the number set (digits only): ",
                             "^[0-9]+$", "Invalid input. Please enter digits only.")
    filepath = input("Enter the PDF file path: ")
    return char_set, num_set, filepath


def generate_passwords(char_set, num_set):
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


def check_password(pdf_filepath, password, start_time):
    try:
        with open(pdf_filepath, 'rb') as pdf_file:
            pdfReader = PyPDF2.PdfReader(pdf_file)
            if pdfReader.decrypt(password) == 1:
                return password, time.time() - start_time
            else:
                return None, time.time() - start_time
    except Exception as e:
        print(f'Error occurred with password {password}: {e}')
        return None, time.time() - start_time

if __name__ == '__main__':
    init(autoreset=True)  # Initialize colorama
    char_set, num_set, filepath = get_user_inputs()
    clear_terminal()  # Clear inputs once cracking starts

    passwords = generate_passwords(char_set, num_set)
    start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_password = {executor.submit(check_password, filepath, password, start_time): password for password in passwords}
        attempt_num = 0

        for future in concurrent.futures.as_completed(future_to_password):
            password = future_to_password[future]
            attempt_num += 1
            decrypted_password, elapsed_time = future.result()

            if decrypted_password is not None:
                print(f'\n{Fore.GREEN}Password found: {decrypted_password}{Style.RESET_ALL}')
                break

            sys.stdout.write(f'\r{Fore.YELLOW}Attempt {attempt_num}: {password}, Elapsed time: {elapsed_time:.2f} seconds{Style.RESET_ALL}')
            sys.stdout.flush()
