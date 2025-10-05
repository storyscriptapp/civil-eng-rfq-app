"""
Simple authentication system for RFQ Tracker
"""
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import hashlib
import os

security = HTTPBasic()

# Default credentials (CHANGE THESE!)
# You can also set via environment variables for better security
USERNAME = os.getenv("RFQ_USERNAME", "admin")
# Password: "changeme123" (hashed with SHA256)
PASSWORD_HASH = os.getenv("RFQ_PASSWORD_HASH", "494a715f7e9b4071aca61bac42ca858a309524e5864f0920030862a4ae7589be")

def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return hash_password(plain_password) == hashed_password

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Verify HTTP Basic Authentication
    Returns username if valid, raises HTTPException if not
    """
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = verify_password(credentials.password, PASSWORD_HASH)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username


# Utility function to generate password hash
if __name__ == "__main__":
    print("\n=== Password Hash Generator ===")
    password = input("Enter password to hash: ")
    print(f"\nHashed password: {hash_password(password)}")
    print("\nAdd this to your environment variables:")
    print(f'RFQ_PASSWORD_HASH="{hash_password(password)}"')

