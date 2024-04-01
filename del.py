from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Generate RSA key pair
key = RSA.generate(2048)

# Extract public and private keys
public_key = key.publickey()
private_key = key

# Encrypt message using public key
def encrypt_message(message, public_key):
    cipher = PKCS1_OAEP.new(public_key)
    encrypted_message = cipher.encrypt(message.encode())
    return encrypted_message.decode()

# Decrypt message using private key
def decrypt_message(encrypted_message, private_key):
    cipher = PKCS1_OAEP.new(private_key)
    decrypted_message = cipher.decrypt(encrypted_message)
    return decrypted_message.decode()

# Example usage
message = "This is a secret message."
encrypted_message = encrypt_message(message, public_key)
print("Encrypted message:", encrypted_message)

decrypted_message = decrypt_message(encrypted_message, private_key)
print("Decrypted message:", decrypted_message)
