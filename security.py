import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# In a real app, this key would be stored in a .env file.
# For our simulation, we use a fixed 32-byte key (256 bits).
SECRET_KEY = b'EMsync_Secret_Key_2025_Phase_3!!' 

def encrypt_patient_data(data_string):
    """
    Encrypts a string (e.g., 'Alan Joseph|Critical|Hypoxia') into an AES-256 ciphertext.
    """
    # Generate a random Initialization Vector (IV) for every encryption
    iv = get_random_bytes(16)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    
    # Pad and encrypt the data
    ct_bytes = cipher.encrypt(pad(data_string.encode('utf-8'), AES.block_size))
    
    # Combine IV and Ciphertext, then encode to Base64 for easy transport
    result = base64.b64encode(iv + ct_bytes).decode('utf-8')
    return result

def decrypt_patient_data(encrypted_id):
    """
    Decrypts the AES-256 Transfer ID back into readable patient data.
    """
    try:
        # Decode from Base64
        raw_data = base64.b64decode(encrypted_id)
        
        # Extract the first 16 bytes (IV) and the rest (Ciphertext)
        iv = raw_data[:16]
        ct = raw_data[16:]
        
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
        
        # Decrypt and remove padding
        pt = unpad(cipher.decrypt(ct), AES.block_size).decode('utf-8')
        return pt
    except Exception as e:
        return f"Decryption Failed: {str(e)}"

# --- Simple Test Section ---
if __name__ == "__main__":
    sample_data = "Patient: John Doe | Urgency: Critical | Needs: Ventilator"
    print(f"Original Data: {sample_data}")
    
    encrypted = encrypt_patient_data(sample_data)
    print(f"\nGenerated Transfer ID (Encrypted): {encrypted}")
    
    decrypted = decrypt_patient_data(encrypted)
    print(f"\nDecrypted Data at Hospital: {decrypted}")