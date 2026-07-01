import requests

BASE_URL = "http://127.0.0.1:8000"

def test_signup():
    email = "test@example.com"
    name = "Test User"
    password = "password123"

    print("Requesting OTP...")
    res = requests.post(f"{BASE_URL}/auth/request-otp", json={"name": name, "email": email})
    print(res.status_code, res.json())
    if res.status_code != 200:
        return

    # To get the OTP, we'll have to read it from the backend memory for testing, but let's see if this succeeds.
    # We can modify auth.py temporarily to return the OTP just for testing, or print it.

if __name__ == "__main__":
    test_signup()
