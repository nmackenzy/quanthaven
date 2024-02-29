import os

KEY_FILE = 'keys.key'


def generate_key(length):
    return ''.join(chr(os.urandom(1)[0]) for _ in range(length))


def store_key(identifier, key):
    with open(KEY_FILE, 'a') as file:
        file.write(f"{identifier}:{key}\n")


def retrieve_key(identifier):
    with open(KEY_FILE, 'r') as file:
        for line in file.readlines():
            if line.startswith(f"{identifier}:"):
                return line.strip().split(':')[1]
    raise ValueError(f"No key found for identifier {identifier}")


def encrypt_data(string_to_encrypt, identifier):
    key = generate_key(len(string_to_encrypt))
    store_key(identifier, key)
    return ''.join(chr(ord(p) ^ ord(k)) for p, k in zip(string_to_encrypt, key))


def decrypt_data(encrypted_string, identifier):
    key = retrieve_key(identifier)
    return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(encrypted_string, key))
