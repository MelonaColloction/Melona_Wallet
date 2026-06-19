import json
import os
import secrets
import time

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class MelonaToken:
    def __init__(self):
        self.db_file = "melona_data.json"
        self.min_buy = 0.01
        self.max_balance = 0.01
        self.sell_percent = 0.5
        self.TOTAL_SUPPLY = 5000000
        self.owner_address = "MLEb4ed27e5103efdbdd5031053fba5cdfa7706bbaf"
        
        self.data = self._load()
        if self.owner_address not in self.data["wallets"]:
            self._create_owner()
    
    def _load(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    if "saved_keys" not in data:
                        data["saved_keys"] = {}
                    if "history" not in data:
                        data["history"] = []
                    if "balances" not in data:
                        data["balances"] = {}
                    if "wallets" not in data:
                        data["wallets"] = {}
                    return data
            except:
                return self._default()
        return self._default()
    
    def _default(self):
        return {
            "wallets": {},
            "balances": {},
            "history": [],
            "saved_keys": {}
        }
    
    def _save(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def _create_owner(self):
        owner_private_key = "d640a76ad5a2249a95155f0bebe368048d6a2d64e8cc2e20030b4c516d42ece5"
        self.data["wallets"][self.owner_address] = owner_private_key
        self.data["balances"][self.owner_address] = str(self.TOTAL_SUPPLY)
        self.data["saved_keys"][self.owner_address] = {
            "name": "OWNER",
            "private_key": owner_private_key,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "is_owner": True
        }
        self.data["history"].append(f"OWNER INITIALIZED {self.TOTAL_SUPPLY:,} MLE  {time.strftime('%H:%M')}")
        self._save()
    
    def is_owner(self, addr):
        return addr == self.owner_address
    
    def create_wallet(self, name=None):
        addr = "MLE" + secrets.token_hex(20)
        priv = secrets.token_hex(32)
        self.data["wallets"][addr] = priv
        self.data["balances"][addr] = "0.0"
        if not name or name.strip() == "":
            name = addr[:8]
        self.data["saved_keys"][addr] = {
            "name": name,
            "private_key": priv,
            "created": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save()
        return addr, priv
    
    def recover_wallet(self, private_key):
        private_key = private_key.strip()
        for addr, priv in self.data["wallets"].items():
            if priv == private_key:
                return addr
        addr = "MLE" + secrets.token_hex(20)
        self.data["wallets"][addr] = private_key
        self.data["balances"][addr] = "0.0"
        self.data["saved_keys"][addr] = {
            "name": "Recovered",
            "private_key": private_key,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "recovered": True
        }
        self._save()
        return addr
    
    def get_balance(self, addr):
        return float(self.data["balances"].get(addr, "0.0"))
    
    def wallet_exists(self, addr):
        return addr in self.data["wallets"]
    
    def get_circulation(self):
        total = 0
        for bal in self.data["balances"].values():
            total += float(bal)
        return total
    
    def buy(self, addr, amount=None):
        bal = self.get_balance(addr)
        circulation = self.get_circulation()
        
        if circulation >= self.TOTAL_SUPPLY:
            return False, f"Total supply ({self.TOTAL_SUPPLY:,} MLE) exhausted"
        
        if self.is_owner(addr):
            if amount is None:
                amount = 100.0
            else:
                amount = float(amount)
            
            remaining = self.TOTAL_SUPPLY - circulation
            if amount > remaining:
                amount = remaining
            if amount <= 0:
                return False, "No supply remaining"
            
            self.data["balances"][addr] = str(bal + amount)
            self.data["history"].append(f"OWNER BUY {amount:.4f} MLE  {time.strftime('%H:%M')}")
            self._save()
            return True, self.get_balance(addr)
        
        if bal + self.min_buy > self.max_balance:
            return False, f"Max balance per wallet is {self.max_balance} MLE"
        
        remaining = self.TOTAL_SUPPLY - circulation
        if self.min_buy > remaining:
            return False, f"Only {remaining:.4f} MLE remaining"
        
        self.data["balances"][addr] = str(bal + self.min_buy)
        self.data["history"].append(f"BUY {self.min_buy} MLE  {time.strftime('%H:%M')}")
        self._save()
        return True, self.get_balance(addr)
    
    def sell(self, addr, amount=None):
        bal = self.get_balance(addr)
        if bal == 0:
            return False, "No balance"
        
        if self.is_owner(addr):
            if amount is None:
                print(f"\n{Colors.YELLOW}Your balance: {bal:,.4f} MLE{Colors.END}")
                amount_input = input(f"{Colors.BOLD}Enter amount to sell (or Enter for all): {Colors.END}").strip()
                if amount_input == "":
                    amount = bal
                else:
                    try:
                        amount = float(amount_input)
                        if amount <= 0:
                            return False, "Amount must be positive"
                        if amount > bal:
                            return False, f"Insufficient balance. You have {bal:,.4f} MLE"
                    except:
                        return False, "Invalid amount"
            else:
                amount = float(amount)
                if amount <= 0:
                    return False, "Amount must be positive"
                if amount > bal:
                    return False, f"Insufficient balance. You have {bal:,.4f} MLE"
            
            new_bal = bal - amount
            self.data["balances"][addr] = str(new_bal)
            self.data["history"].append(f"OWNER SELL {amount:.4f} MLE  {time.strftime('%H:%M')}")
            self._save()
            return True, new_bal
        
        amount = bal * self.sell_percent
        new_bal = bal - amount
        self.data["balances"][addr] = str(new_bal)
        self.data["history"].append(f"SELL {amount:.4f} MLE  {time.strftime('%H:%M')}")
        self._save()
        return True, new_bal
    
    def distribute(self, from_addr, to_addr, amount):
        if not self.is_owner(from_addr):
            return False, "Only owner can distribute tokens"
        if not self.wallet_exists(to_addr):
            return False, "Recipient wallet not found"
        
        amount = float(amount)
        if amount <= 0:
            return False, "Amount must be positive"
        
        bal = self.get_balance(from_addr)
        if amount > bal:
            return False, f"Insufficient balance. You have {bal:.4f} MLE"
        
        new_bal_from = bal - amount
        new_bal_to = self.get_balance(to_addr) + amount
        self.data["balances"][from_addr] = str(new_bal_from)
        self.data["balances"][to_addr] = str(new_bal_to)
        self.data["history"].append(f"DISTRIBUTE {amount:.4f} MLE  {to_addr[:10]}...  {time.strftime('%H:%M')}")
        self._save()
        return True, new_bal_from
    
    def transfer(self, from_addr, to_addr, amount):
        if not self.wallet_exists(from_addr):
            return False, "Sender wallet not found"
        if not self.wallet_exists(to_addr):
            return False, "Recipient wallet not found"
        if from_addr == to_addr:
            return False, "Cannot transfer to yourself"
        
        bal = self.get_balance(from_addr)
        amount = float(amount)
        if amount <= 0:
            return False, "Amount must be positive"
        if amount > bal:
            return False, f"Insufficient balance. You have {bal:.4f} MLE"
        
        if not self.is_owner(from_addr) and amount > self.max_balance:
            return False, f"Max transfer {self.max_balance} MLE"
        
        new_bal_from = bal - amount
        new_bal_to = self.get_balance(to_addr) + amount
        self.data["balances"][from_addr] = str(new_bal_from)
        self.data["balances"][to_addr] = str(new_bal_to)
        self.data["history"].append(f"TRANSFER {amount:.4f} MLE  {from_addr[:10]}... → {to_addr[:10]}...  {time.strftime('%H:%M')}")
        self._save()
        return True, new_bal_from
    
    def show_private_key(self, addr):
        if addr in self.data["wallets"]:
            priv = self.data["wallets"][addr]
            name = self.data["saved_keys"].get(addr, {}).get("name", "Unknown")
            return priv, name
        return None, None
    
    def list_wallets(self):
        wallets = []
        for addr in self.data["wallets"]:
            name = self.data["saved_keys"].get(addr, {}).get("name", "Unknown")
            balance = self.get_balance(addr)
            is_owner = self.is_owner(addr)
            wallets.append((addr, name, balance, is_owner))
        return wallets
    
    def get_stats(self):
        circulation = self.get_circulation()
        remaining = self.TOTAL_SUPPLY - circulation
        return {
            "total_supply": self.TOTAL_SUPPLY,
            "circulation": circulation,
            "remaining": remaining,
            "total_wallets": len(self.data["wallets"]),
            "total_transactions": len(self.data["history"]),
            "owner": self.owner_address,
            "owner_balance": self.get_balance(self.owner_address)
        }


def print_header():
    os.system('clear')
    print(f"{Colors.BOLD}{Colors.GREEN}")
    print("🍉" * 20)
    print("        M E L O N A   W A L L E T")
    print("🍉" * 20)
    print(f"{Colors.END}")

def print_menu():
    print(f"{Colors.YELLOW}{Colors.BOLD}")
    print("📋 MAIN MENU")
    print(f"{Colors.END}")
    print(f"{Colors.CYAN}1.{Colors.END} Create Wallet")
    print(f"{Colors.CYAN}2.{Colors.END} Recover Wallet")
    print(f"{Colors.GREEN}3.{Colors.END} Buy")
    print(f"{Colors.RED}4.{Colors.END} Sell")
    print(f"{Colors.BLUE}5.{Colors.END} Transfer")
    print(f"{Colors.BOLD}{Colors.YELLOW}6.{Colors.END} Distribute (Owner Only)")
    print(f"{Colors.YELLOW}7.{Colors.END} Balance")
    print(f"{Colors.BOLD}8.{Colors.END} Show Private Key")
    print(f"{Colors.CYAN}9.{Colors.END} List All Wallets")
    print(f"{Colors.BLUE}10.{Colors.END} History")
    print(f"{Colors.BOLD}{Colors.RED}11.{Colors.END} Stats")
    print(f"{Colors.RED}0.{Colors.END} Exit")
    print("-" * 40)

def main():
    token = MelonaToken()
    address = None
    
    while True:
        print_header()
        
        if address:
            bal = token.get_balance(address)
            name = token.data["saved_keys"].get(address, {}).get("name", "Unknown")
            if token.is_owner(address):
                print(f"{Colors.GREEN}👑 OWNER MODE{Colors.END}  |  {Colors.YELLOW}Balance: {bal:,.4f} MLE{Colors.END}\n")
            else:
                print(f"{Colors.GREEN}🔑 Active: {Colors.BOLD}{name}{Colors.END}  |  {Colors.YELLOW}Balance: {bal:.4f} MLE{Colors.END}\n")
        else:
            print(f"{Colors.RED}🔑 No wallet loaded{Colors.END}\n")
        
        print_menu()
        
        choice = input(f"{Colors.BOLD}>> {Colors.END}")
        
        if choice == "1":
            name = input("Enter wallet name (or Enter for auto): ").strip()
            if not name:
                name = None
            addr, priv = token.create_wallet(name)
            address = addr
            print(f"\n{Colors.GREEN}✅ Wallet created!{Colors.END}")
            print(f"{Colors.YELLOW}Name:{Colors.END} {token.data['saved_keys'][addr]['name']}")
            print(f"{Colors.YELLOW}Address:{Colors.END} {addr}")
            print(f"{Colors.RED}Private Key:{Colors.END} {priv}")
            print(f"{Colors.GREEN}Balance:{Colors.END} {token.get_balance(addr):.4f} MLE")
            print(f"\n{Colors.RED}⚠️ SAVE YOUR PRIVATE KEY!{Colors.END}")
            input("\nPress Enter to continue...")
        
        elif choice == "2":
            priv_key = input("Enter your private key: ").strip()
            if not priv_key:
                print(f"{Colors.RED}❌ Private key cannot be empty{Colors.END}")
                input("Press Enter to continue...")
                continue
            addr = token.recover_wallet(priv_key)
            address = addr
            print(f"\n{Colors.GREEN}✅ Wallet recovered!{Colors.END}")
            print(f"{Colors.YELLOW}Address:{Colors.END} {addr}")
            print(f"{Colors.GREEN}Balance:{Colors.END} {token.get_balance(addr):.4f} MLE")
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            if not address:
                print(f"{Colors.RED}❌ Create or recover wallet first{Colors.END}")
                input("Press Enter to continue...")
                continue
            
            if token.is_owner(address):
                amount = input("Enter amount to buy (or Enter for 100): ").strip()
                if not amount:
                    amount = 100
                else:
                    try:
                        amount = float(amount)
                    except:
                        print(f"{Colors.RED}❌ Invalid amount{Colors.END}")
                        input("Press Enter to continue...")
                        continue
                ok, result = token.buy(address, amount)
            else:
                ok, result = token.buy(address)
            
            if ok:
                print(f"{Colors.GREEN}✅ Buy successful!{Colors.END}")
                print(f"   Balance: {result:.4f} MLE")
            else:
                print(f"{Colors.RED}❌ {result}{Colors.END}")
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            if not address:
                print(f"{Colors.RED}❌ Create or recover wallet first{Colors.END}")
                input("Press Enter to continue...")
                continue
            ok, result = token.sell(address)
            if ok:
                print(f"{Colors.GREEN}✅ Sell successful!{Colors.END}")
                print(f"   Balance: {result:.4f} MLE")
            else:
                print(f"{Colors.RED}❌ {result}{Colors.END}")
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            if not address:
                print(f"{Colors.RED}❌ Create or recover wallet first{Colors.END}")
                input("Press Enter to continue...")
                continue
            
            if token.is_owner(address):
                bal = token.get_balance(address)
                print(f"{Colors.YELLOW}Your balance: {bal:,.4f} MLE{Colors.END}")
            
            to_addr = input("Enter recipient address: ").strip()
            if not to_addr:
                print(f"{Colors.RED}❌ Address cannot be empty{Colors.END}")
                input("Press Enter to continue...")
                continue
            
            amount = input("Enter amount to transfer: ").strip()
            if not amount:
                print(f"{Colors.RED}❌ Amount cannot be empty{Colors.END}")
                input("Press Enter to continue...")
                continue
            
            try:
                amount_float = float(amount)
            except:
                print(f"{Colors.RED}❌ Invalid amount{Colors.END}")
                input("Press Enter to continue...")
                continue
            
            ok, result = token.transfer(address, to_addr, amount_float)
            if ok:
                print(f"{Colors.GREEN}✅ Transfer successful!{Colors.END}")
                print(f"   New balance: {result:.4f} MLE")
                print(f"   Recipient balance: {token.get_balance(to_addr):.4f} MLE")
            else:
                print(f"{Colors.RED}❌ {result}{Colors.END}")
            input("\nPress Enter to continue...")
        
        elif choice == "6":
            if not address:
                print(f"{Colors.RED}❌ Create or recover wallet first{Colors.END}")
                input("Press Enter to continue...")
                continue
            if not token.is_owner(address):
                print(f"{Colors.RED}❌ Only OWNER can distribute tokens!{Colors.END}")
                input("Press Enter to continue...")
                continue
            to_addr = input("Enter recipient address: ").strip()
            if not to_addr:
                print(f"{Colors.RED}❌ Address cannot be empty{Colors.END}")
                input("Press Enter to continue...")
                continue
            if not token.wallet_exists(to_addr):
                print(f"{Colors.RED}❌ Wallet not found{Colors.END}")
                input("Press Enter to continue...")
                continue
            amount = input("Enter amount to distribute: ").strip()
            if not amount:
                print(f"{Colors.RED}❌ Amount cannot be empty{Colors.END}")
                input("Press Enter to continue...")
                continue
            try:
                amount_float = float(amount)
            except:
                print(f"{Colors.RED}❌ Invalid amount{Colors.END}")
                input("Press Enter to continue...")
                continue
            ok, result = token.distribute(address, to_addr, amount_float)
            if ok:
                print(f"{Colors.GREEN}✅ Distribution successful!{Colors.END}")
                print(f"   New balance: {result:.4f} MLE")
                print(f"   Recipient balance: {token.get_balance(to_addr):.4f} MLE")
            else:
                print(f"{Colors.RED}❌ {result}{Colors.END}")
            input("\nPress Enter to continue...")
        
        elif choice == "7":
            if not address:
                print(f"{Colors.RED}❌ Create or recover wallet first{Colors.END}")
                input("Press Enter to continue...")
                continue
            bal = token.get_balance(address)
            name = token.data["saved_keys"].get(address, {}).get("name", "Unknown")
            if token.is_owner(address):
                print(f"{Colors.GREEN}👑 OWNER{Colors.END} {Colors.YELLOW}{name}{Colors.END} Balance: {Colors.GREEN}{bal:,.4f} MLE{Colors.END}")
            else:
                print(f"{Colors.YELLOW}💰 {name}{Colors.END} Balance: {Colors.GREEN}{bal:.4f} MLE{Colors.END}")
            input("\nPress Enter to continue...")
        
        elif choice == "8":
            if not address:
                print(f"{Colors.RED}❌ Create or recover wallet first{Colors.END}")
                input("Press Enter to continue...")
                continue
            priv, name = token.show_private_key(address)
            if priv:
                print(f"\n{Colors.RED}🔑 Private Key for '{name}':{Colors.END}")
                print(f"{Colors.BOLD}{priv}{Colors.END}")
                print(f"\n{Colors.RED}⚠️ NEVER share this with anyone!{Colors.END}")
            else:
                print(f"{Colors.RED}❌ Wallet not found{Colors.END}")
            input("\nPress Enter to continue...")
        
        elif choice == "9":
            wallets = token.list_wallets()
            if not wallets:
                print(f"{Colors.RED}No wallets found{Colors.END}")
            else:
                print(f"\n{Colors.CYAN}📋 ALL WALLETS:{Colors.END}")
                print("-" * 50)
                for addr, name, balance, is_owner in wallets:
                    owner_tag = f"{Colors.GREEN}👑 OWNER{Colors.END}" if is_owner else ""
                    if is_owner:
                        print(f"{Colors.YELLOW}{name}{Colors.END}: {addr[:20]}...  {Colors.GREEN}{balance:,.4f} MLE{Colors.END} {owner_tag}")
                    else:
                        print(f"{Colors.YELLOW}{name}{Colors.END}: {addr[:20]}...  {Colors.GREEN}{balance:.4f} MLE{Colors.END} {owner_tag}")
                print("-" * 50)
            input("\nPress Enter to continue...")
        
        elif choice == "10":
            history = token.data["history"][-8:][::-1]
            if not history:
                print(f"{Colors.RED}📜 No transactions{Colors.END}")
            else:
                print(f"\n{Colors.CYAN}📜 RECENT TRANSACTIONS:{Colors.END}")
                print("-" * 50)
                for h in history:
                    if "BUY" in h or "DISTRIBUTE" in h:
                        print(f"{Colors.GREEN}{h}{Colors.END}")
                    elif "SELL" in h:
                        print(f"{Colors.RED}{h}{Colors.END}")
                    elif "OWNER" in h:
                        print(f"{Colors.YELLOW}{h}{Colors.END}")
                    else:
                        print(f"{Colors.BLUE}{h}{Colors.END}")
                print("-" * 50)
            input("\nPress Enter to continue...")
        
        elif choice == "11":
            stats = token.get_stats()
            print(f"\n{Colors.CYAN}📊 BLOCKCHAIN STATISTICS:{Colors.END}")
            print("-" * 40)
            print(f"{Colors.YELLOW}Total Supply:{Colors.END} {stats['total_supply']:,} MLE")
            print(f"{Colors.GREEN}Circulation:{Colors.END} {stats['circulation']:,.4f} MLE")
            print(f"{Colors.RED}Remaining:{Colors.END} {stats['remaining']:,.4f} MLE")
            print(f"{Colors.CYAN}Total Wallets:{Colors.END} {stats['total_wallets']}")
            print(f"{Colors.BLUE}Total Transactions:{Colors.END} {stats['total_transactions']}")
            print(f"{Colors.GREEN}Owner Balance:{Colors.END} {stats['owner_balance']:,.4f} MLE")
            print("-" * 40)
            input("\nPress Enter to continue...")
        
        elif choice == "0":
            print(f"\n{Colors.GREEN}👋 Goodbye!{Colors.END}")
            break
        
        else:
            print(f"{Colors.RED}❌ Invalid choice{Colors.END}")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()