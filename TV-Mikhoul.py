import os
import re
import concurrent.futures
import requests
import subprocess

class FolderM3UCollector:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def validate_stream(self, link_tuple):
        info, url = link_tuple
        try:
            response = requests.head(url, timeout=3, allow_redirects=True)
            if response.status_code == 200: 
                return "ACTIVE", info, url
        except:
            pass
        return "INACTIVE", info, url

    def upload_to_github(self):
        print("\n-> Sincronizare automata cu GitHub...")
        try:
            # Rulam comenzile Git in fundal
            subprocess.run(["git", "init"], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", "Actualizare automata canale si filme 2026"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Trimitem datele online
            subprocess.run(["git", "push", "-u", "origin", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("\033[92m[✓ SUCCESS] Lista a fost incarcata in contul tau de GitHub!\033[0m")
        except Exception as e:
            print(f"Nota Git: Seteaza conexiunea initiala daca este prima rulare. Detalii: {e}")

    def process_folder(self):
        if not os.path.exists(self.folder_path):
            print(f"\n\033[91m⚠️ EROARE: Nu am gasit folderul '{self.folder_path}'!\033[0m")
            return

        raw_links = []
        print("\n=============================================")
        print(f"1. Scanare FOLDER si baze de date online...")
        print("=============================================")
        
        # Citire din folderul tau local
        for root, dirs, files in os.walk(self.folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(('.m3u', '.m3u8', '.txt', '.list')):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            current_info = ""
                            for line in f.read().splitlines():
                                line = line.strip()
                                if line.startswith("#EXTINF"): current_info = line
                                elif line.startswith("http"): raw_links.append((current_info, line))
                    except: pass

        # Adaugam si bazele online direct ca sa avem filme din 2026 mereu proaspete
        online_urls = [
            "https://githubusercontent.com",
            "https://githubusercontent.com"
        ]
        for url in online_urls:
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200:
                    current_info = ""
                    for line in res.text.splitlines():
                        line = line.strip()
                        if line.startswith("#EXTINF"): current_info = line
                        elif line.startswith("http"): raw_links.append((current_info, line))
            except: pass

        unique_links = list(set(raw_links))
        print(f"\nAm gasit {len(unique_links)} link-uri unice.")
        print("Incepe testarea conexiunilor active...\n")

        valid_channels = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(self.validate_stream, link) for link in unique_links]
            for future in concurrent.futures.as_completed(futures):
                status, info, url = future.result()
                name = info.split(",")[-1] if "," in info else "Canal TV"
                if status == "ACTIVE":
                    print(f"\033[92m[✓ FUNCTIONAL] -> {name}\033[0m")
                    valid_channels.append((info, url))

        output_path = "LiveTV.m3u"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for info, url in valid_channels:
                f.write(f"{info}\n{url}\n")
                
        print(f"\nAu ramas {len(valid_channels)} link-uri active.")
        
        # Chemam functia care urca lista pe GitHub automat
        self.upload_to_github()

if __name__ == "__main__":
    collector = FolderM3UCollector("lista_veche.m3u")
    collector.process_folder()
