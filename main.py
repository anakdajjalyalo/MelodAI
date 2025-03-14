import json
import random
import string
import asyncio
import aiohttp
import cloudscraper
import re
import time
from termcolor import colored
from time import sleep
from bs4 import BeautifulSoup
from eth_account import Account

def rainbow_banner():
    text = """
╔╦╗╔═╗╦  ╔═╗╔╦╗  ╔═╗╦
║║║║╣ ║  ║ ║ ║║  ╠═╣║
╩ ╩╚═╝╩═╝╚═╝═╩╝  ╩ ╩╩ 

    
    """
    colors = ['red', 'yellow', 'green', 'cyan', 'blue', 'magenta']
    for line in text.split("\n"):
        colored_line = "".join(colored(char, random.choice(colors)) for char in line)
        print(colored_line)
        time.sleep(0.1)

class AutoRegisterBot:
    def __init__(self, num_accounts, invite_code):
        self.scraper = cloudscraper.create_scraper()
        self.num_accounts = num_accounts
        self.invite_code = invite_code

    def generate_random_domain(self):
        vowels = 'aeiou'
        consonants = 'bcdfghjklmnpqrstvwxyz'
        keyword = random.choice(consonants) + random.choice(vowels)
        url = f'https://generator.email/search.php?key={keyword}'
        for _ in range(3):
            response = self.scraper.get(url)
            if response.status_code == 200:
                try:
                    domains = response.json()
                    valid_domains = [d for d in domains if all(ord(c) < 128 for c in d)]
                    if valid_domains:
                        return random.choice(valid_domains)
                except json.JSONDecodeError:
                    pass
            sleep(5)
        return None

    def generate_random_email(self, domain):
        first_name = "".join(random.choices(string.ascii_lowercase, k=5))
        last_name = "".join(random.choices(string.ascii_lowercase, k=5))
        random_nums = "".join(random.choices(string.digits, k=3))
        separator = random.choice(["", "."])
        email = f"{first_name}{separator}{last_name}{random_nums}@{domain}"
        
        with open("emails.txt", "a") as f:
            f.write(email + "\n")
        
        return email

    def generate_wallet(self):
        account = Account.create()
        wallet_address = account.address
        private_key = account.key.hex()
        with open("wallets.txt", "a") as f:
            f.write(f"{wallet_address}|{private_key}\n")
        return wallet_address

    async def register_email(self, email):
        url = "https://hamster.xar.name/index.php/api/v1/send_r_email"
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "Referer": "https://web.melodai.pro/",
        }
        data = json.dumps({"email": email, "type": 0})

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    print(f"✅ Berhasil mendaftarkan email: {email}")
                    return True
                else:
                    print(f"❌ Gagal register {email}, Status: {response.status}")
                    return False

    async def get_verification_code(self, email, domain):
        cookies = {'embx': f'[%22{email}%22]', 'surl': f'{domain}/{email.split("@")[0]}'}
        headers = {'User-Agent': self.scraper.headers['User-Agent']}
        
        for attempt in range(5):
            print(f"🔍 Mencari kode verifikasi untuk {email}... Percobaan {attempt + 1}/5")
            response = self.scraper.get('https://generator.email/inbox1/', headers=headers, cookies=cookies)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                email_text = soup.get_text()
                otp_match = re.search(r'\b\d{6}\b', email_text)
                if otp_match:
                    otp_code = otp_match.group(0)
                    print(f"✅ Kode verifikasi ditemukan: {otp_code}")
                    return otp_code
            
            await asyncio.sleep(10)
        
        print("❌ Gagal mendapatkan kode verifikasi setelah 5 percobaan.")
        return None

    async def login_with_otp(self, email, otp_code):
        url = "https://hamster.xar.name/index.php/api/v1/login_email"
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "Referer": "https://web.melodai.pro/",
        }
        data = json.dumps({"email": email, "code": otp_code, "invite_code": self.invite_code, "platform": 2})

        for attempt in range(10):
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        resp_json = await response.json()
                        user_data = resp_json.get("data", {}).get("user_data", {})
                        member_id = user_data.get("id")
                        token = user_data.get("token")
                        print(f"✅ Berhasil login! Member ID: {member_id}, Token: {token}")
                        
                        with open("token.txt", "a") as f:
                            f.write(f"{token}|{member_id}\n")
                        
                        return member_id, token
                    else:
                        print(f"❌ Gagal login {email}, percobaan ke-{attempt + 1}/10")
            
        print("❌ Gagal login setelah 10 percobaan. Mencoba email berikutnya...")
        return None, None

    async def bind_wallet(self, member_id, token, wallet_address):
        url = "https://hamster.xar.name/index.php/api/v1/bind_wallet"
        headers = {
            "accept": "application/json, text/plain, */*",
            "authorization": token,
            "content-type": "application/json",
            "Referer": "https://web.melodai.pro/",
        }
        data = json.dumps({"member_id": member_id, "wallet": wallet_address})
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    print(f"✅ Wallet {wallet_address} berhasil di-bind!")
                else:
                    print(f"❌ Gagal bind wallet, Status: {response.status}")

async def main():
    rainbow_banner()
    num_accounts = int(input("Masukkan jumlah akun yang ingin dibuat: "))
    invite_code = input("Masukkan kode referral: ")
    bot = AutoRegisterBot(num_accounts, invite_code)
    
    for _ in range(num_accounts):
        domain = bot.generate_random_domain()
        if domain:
            email = bot.generate_random_email(domain)
            print(f"📧 Email yang digunakan: {email}")
            if await bot.register_email(email):
                otp_code = await bot.get_verification_code(email, domain)
                if otp_code:
                    member_id, token = await bot.login_with_otp(email, otp_code)
                    if member_id and token:
                        wallet_address = bot.generate_wallet()
                        print(f"💰 Wallet Generated: {wallet_address}")
                        await bot.bind_wallet(member_id, token, wallet_address)

if __name__ == "__main__":
    asyncio.run(main())
