import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Example passwords for trainers
trainers = {
    "Ava Strong": "trainer123",
    "Taylor Flexman": "trainer123",
    "Max Steele": "trainer123",
    "Sierra Powers": "trainer123"
}

for name, pw in trainers.items():
    print(f"{name}: {hash_password(pw)}")
