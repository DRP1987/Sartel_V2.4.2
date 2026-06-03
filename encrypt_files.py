"""Encrypt sensitive files before building executable."""

import os
import sys
from utils.security import SecurityManager

def encrypt_all_files():
    """Encrypt configuration and documentation files."""
    
    security = SecurityManager()
    
    print("🔐 Encrypting sensitive files.. .\n")
    
    # Files to encrypt - ADD YOUR FILES HERE
    files_to_encrypt = [
        ('config/configurations.json', 'config/configurations.json. enc'),
    ]
    
    # Find all PDF files in config/docs
    docs_folder = 'config/docs'
    if os.path.exists(docs_folder):
        for filename in os.listdir(docs_folder):
            if filename.endswith('.pdf'):
                source = os.path.join(docs_folder, filename)
                encrypted = source + '.enc'
                files_to_encrypt.append((source, encrypted))
    
    # Encrypt each file
    success_count = 0
    for source, encrypted in files_to_encrypt:
        if os.path.exists(source):
            try:
                security.encrypt_file(source, encrypted)
                success_count += 1
            except Exception as e:
                print(f"❌ Failed to encrypt {source}: {e}")
        else:
            print(f"⚠️  Warning: {source} not found, skipping")
    
    print(f"\n✅ Encryption complete! {success_count}/{len(files_to_encrypt)} files encrypted")
    print("\n⚠️  IMPORTANT:")
    print("  1. Keep original files in a secure backup location")
    print("  2. The . enc files will be bundled in the executable")
    print("  3. Original files will NOT be included in the build")

if __name__ == "__main__":
    encrypt_all_files()