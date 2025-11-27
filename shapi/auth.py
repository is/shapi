import time
import struct
import hashlib
import random
import os

def bytes_xor(b0:bytes, b1:bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(b0, b1))


def auth_token(key:bytes) -> str:
    nonce_header = struct.pack('<Q', int(time.time() * 1000))
    nonce_random = struct.pack('<I', random.randint(0, 2**32-1))
    nonce_name = key[:4]
    nonce_body = hashlib.sha256(nonce_header + key + nonce_random).digest()[:8]
    
    nonce_header = bytes_xor(nonce_header, nonce_body)
    nonce_name = bytes_xor(nonce_name, nonce_body[:4])
    return (nonce_name + nonce_header + nonce_random + nonce_body ).hex()


def token_verify(token_str:str, keys:dict[bytes, bytes]) -> bytes|None:
    nonce = bytes.fromhex(token_str)
    if len(nonce) != 24:
        return None
    
    nonce_name = nonce[:4]
    nonce_header = nonce[4:12]
    nonce_random = nonce[12:16]
    nonce_body = nonce[16:]

    nonce_name = bytes_xor(nonce_name, nonce_body[:4])
    nonce_header = bytes_xor(nonce_header, nonce_body)

    nonce_key = keys.get(nonce_name)
    if nonce_key == None:
        return None

    body = hashlib.sha256(nonce_header + nonce_key + nonce_random).digest()[:8]
    if body == nonce_body:
        return nonce_key
    return None

def load_key_from_env():
    return bytes.fromhex(os.environ.get('SHAPI_SECRET_KEY', '33333333333333333333333333333333'))

def load_key_map_from_env() -> dict[bytes, bytes]:
    env_str = os.environ.get('SHAPI_SECRET_KEY', '33333333333333333333333333333333')
    key_str = env_str.split(',')
    keys = [ bytes.fromhex(k) for k in key_str ]
    return { k[:4]:k for k in keys }