"""
Generate a password hash for the RFQ Tracker authentication
"""
import hashlib

# Get the new password from user
new_password = input("Enter your new password: ")
confirm_password = input("Confirm your new password: ")

if new_password != confirm_password:
    print("❌ Passwords don't match!")
    exit(1)

# Generate SHA-256 hash
password_hash = hashlib.sha256(new_password.encode()).hexdigest()

print("\n" + "="*80)
print("✅ Password hash generated!")
print("="*80)
print(f"\nYour new password hash is:\n{password_hash}\n")
print("To update your password:")
print("\n1. On your Jellyfin server, open PowerShell as Administrator")
print("2. Run these commands:")
print(f'\n   [System.Environment]::SetEnvironmentVariable("RFQ_PASSWORD_HASH", "{password_hash}", "Machine")')
print('\n3. Restart the API server (Ctrl+C and restart uvicorn)')
print("\n4. Your new password will be active!")
print("="*80)

