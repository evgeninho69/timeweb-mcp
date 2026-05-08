import argparse
import getpass
import json
import os
import base64

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet


def homedir_path(name):
    return os.path.join(os.path.expanduser("~"), name)


SALT_PATH = homedir_path('.timeweb_credentials.salt')
STORE_PATH = homedir_path('.timeweb_credentials.enc')


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    key = kdf.derive(password.encode())
    return base64.urlsafe_b64encode(key)


def init_store():
    if os.path.exists(SALT_PATH) or os.path.exists(STORE_PATH):
        print('Store already exists. Aborting to avoid overwrite.')
        return
    password = getpass.getpass('Choose master password: ')
    confirm = getpass.getpass('Confirm master password: ')
    if password != confirm:
        print('Passwords do not match.')
        return
    salt = os.urandom(16)
    with open(SALT_PATH, 'wb') as f:
        f.write(salt)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    empty = json.dumps({}).encode()
    token = fernet.encrypt(empty)
    with open(STORE_PATH, 'wb') as f:
        f.write(token)
    os.chmod(SALT_PATH, 0o600)
    os.chmod(STORE_PATH, 0o600)
    print('Initialized encrypted store at', STORE_PATH)


def load_store(password: str):
    if not os.path.exists(SALT_PATH) or not os.path.exists(STORE_PATH):
        raise FileNotFoundError('Store not initialized. Run init first.')
    with open(SALT_PATH, 'rb') as f:
        salt = f.read()
    key = derive_key(password, salt)
    fernet = Fernet(key)
    with open(STORE_PATH, 'rb') as f:
        token = f.read()
    data = fernet.decrypt(token)
    return json.loads(data.decode())


def save_store(data: dict, password: str):
    with open(SALT_PATH, 'rb') as f:
        salt = f.read()
    key = derive_key(password, salt)
    fernet = Fernet(key)
    token = fernet.encrypt(json.dumps(data).encode())
    with open(STORE_PATH, 'wb') as f:
        f.write(token)


def cmd_add(args):
    password = getpass.getpass('Master password: ')
    data = load_store(password)
    svc = args.service
    keyname = args.key
    if svc not in data:
        data[svc] = {}
    if args.value:
        value = args.value
    else:
        value = getpass.getpass('Value: ')
    data[svc][keyname] = value
    save_store(data, password)
    print('Saved', svc, keyname)


def cmd_get(args):
    password = getpass.getpass('Master password: ')
    data = load_store(password)
    svc = args.service
    if svc not in data:
        print('No data for', svc)
        return
    if args.key:
        print(data[svc].get(args.key, 'No such key'))
    else:
        print(json.dumps(data[svc], indent=2))


def cmd_list(args):
    password = getpass.getpass('Master password: ')
    data = load_store(password)
    for svc in data:
        print(svc)


def main():
    p = argparse.ArgumentParser(description='Credential manager for local machine')
    sub = p.add_subparsers(dest='cmd')
    sub_init = sub.add_parser('init')
    sub_init.set_defaults(func=lambda args: init_store())

    sub_add = sub.add_parser('add')
    sub_add.add_argument('service')
    sub_add.add_argument('--key', required=True)
    sub_add.add_argument('--value')
    sub_add.set_defaults(func=cmd_add)

    sub_get = sub.add_parser('get')
    sub_get.add_argument('service')
    sub_get.add_argument('--key')
    sub_get.set_defaults(func=cmd_get)

    sub_list = sub.add_parser('list')
    sub_list.set_defaults(func=cmd_list)

    args = p.parse_args()
    if not args.cmd:
        p.print_help()
        return
    try:
        args.func(args)
    except FileNotFoundError as e:
        print(e)


if __name__ == '__main__':
    main()
