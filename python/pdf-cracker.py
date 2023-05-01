#!/usr/bin/env python3

import itertools
import PyPDF2
import concurrent.futures
import re
import sys
import os
import time
import math
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
        input_list = [item.strip() for item in re.split(',| ', user_input)]  # Split input by commas and spaces, and remove whitespace
        sanitized_input = "".join(sorted(set(input_list), key=input_list.index))  # Remove duplicate characters/numbers
        if re.match(pattern, sanitized_input):
            return sanitized_input
        else:
            print(error_msg)

def get_user_inputs():
    clear_terminal()
    print_banner()

    char_set = sanitize_input(f'{Fore.GREEN}Enter the character set (uppercase letters only): {Style.RESET_ALL}',
                              "^[A-Z]+$", f'\n{Fore.RED}Invalid file path. Please enter uppercase letters only\n{Style.RESET_ALL}')
    num_set = sanitize_input(f'{Fore.GREEN}Enter the number set (digits only): {Style.RESET_ALL}',
                             "^[0-9]+$", f'\n{Fore.RED}Invalid input. Please enter digits only\n{Style.RESET_ALL}')
    filepath = input(f'{Fore.GREEN}Enter the PDF file path: {Style.RESET_ALL}').strip()

    # Check if the file existsf
    while not os.path.isfile(filepath):
        print(f'\n{Fore.RED}Invalid file path. Please enter a valid file path\n{Style.RESET_ALL}')
        filepath = input(f'{Fore.GREEN}Enter the PDF file path: {Style.RESET_ALL}').strip()

    chunk_size = int(input(f'{Fore.GREEN}Enter the chunk size (default: 1000): {Style.RESET_ALL}') or 1000)
    workers = int(input(f'{Fore.GREEN}Enter the number of workers (default: 10): {Style.RESET_ALL}') or 10)

    return char_set, num_set, filepath, chunk_size, workers


def generate_password_chunks(char_set, num_set, chunk_size):
    password_chunks = []
    counter = 0
    for i in range(1, 5):
        char_combos = itertools.product(char_set, repeat=i)
        for char_combo in char_combos:
            num_combos = itertools.product(num_set, repeat=4)
            for num_combo in num_combos:
                password = ''.join(char_combo) + ''.join(num_combo)
                if re.match('^[A-Z]{1,4}[0-9]{4}$', password):
                    password_chunks.append(password)
                    counter += 1
                    if counter == chunk_size:
                        yield password_chunks
                        password_chunks = []
                        counter = 0
    if password_chunks:
        yield password_chunks

class PasswordCracked(Exception):
    def __init__(self, password, elapsed_time):
        self.password = password
        self.elapsed_time = elapsed_time

def check_password(pdf_filepath, password, start_time):
    with open(pdf_filepath, 'rb') as pdf_file:
        pdfReader = PyPDF2.PdfReader(pdf_file)
        if pdfReader.decrypt(password) == 1:
            elapsed_time = time.time() - start_time
            raise PasswordCracked(password, elapsed_time)
        else:
            return None, time.time() - start_time

def worker(pdf_filepath, password_chunk, start_time):
    for password in password_chunk:
        try:
            check_password(pdf_filepath, password, start_time)
            return password, time.time() - start_time
        except PasswordFound as e:
            return str(e), time.time() - start_time
    return None, time.time() - start_time

if __name__ == '__main__':
    init(autoreset=True)  # Initialize colorama
    char_set, num_set, filepath, chunk_size, workers = get_user_inputs()
    clear_terminal()

    total_combinations = sum([(len(char_set) + len(num_set))**i for i in range(5, 9)]) - sum([len(num_set)**i for i in range(5, 9)])
    passwords_generator = generate_password_chunks(char_set, num_set, chunk_size)
    start_time = time.time()

    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_password = {}
        attempt_num = 0

        try:
            progress_bar = tqdm(total=total_combinations, unit='attempt', ncols=100)

            for password_chunk in passwords_generator:
                future_to_password.update({executor.submit(check_password, filepath, password, start_time): password for password in password_chunk})

                for future in concurrent.futures.as_completed(future_to_password):
                    password = future_to_password[future]
                    attempt_num += 1
                    try:
                        decrypted_password, elapsed_time = future.result()
                    except PasswordCracked as e:
                        progress_bar.close()
                        clear_terminal()
                        print(f'{Fore.GREEN}Password found: {e.password}{Style.RESET_ALL}')
                        raise e

                    progress_bar.set_description(f'Attempt {attempt_num}: {password}')
                    progress_bar.update(1)
                
                completed_futures = [future for future in future_to_password if future.done()]
                for future in completed_futures:
                    future_to_password.pop(future)

            progress_bar.close()
            
        except PasswordCracked as e:
            print(f'\n\n{Fore.BLUE}Password cracking finished in {e.elapsed_time:.2f} seconds.{Style.RESET_ALL}')
        except KeyboardInterrupt:
            progress_bar.close()
            clear_terminal()
            print(f'\n\n{Fore.BLUE}Password cracking interrupted by the user.{Style.RESET_ALL}')
            sys.exit(0)
