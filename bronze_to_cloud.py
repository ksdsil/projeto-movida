from supabase import create_client, Client
import os

# ==========================================
# CONFIGURAÇÃO SUPABASE
SUPABASE_URL = os.environ.get("SUPA_URL")
SUPABASE_KEY = os.environ.get("SUPA_KEY")
# ==========================================

def subir_bronze_nuvem():
    caminho_arquivo = "bronze/veiculos_raw.json"
    
    if not os.path.exists(caminho_arquivo):
        print("[!] Arquivo Bronze local não encontrado. Rode o scraper primeiro.")
        return

    print("[*] Conectando ao Supabase Storage...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("[*] Enviando arquivo JSON para o bucket 'bronze-storage'...")
    with open(caminho_arquivo, "rb") as f:
        # Nome do arquivo na nuvem
        nome_nuvem = "veiculos_raw.json"
        # Faz o upload substituindo se já existir
        resposta = supabase.storage.from_("bronze-storage").upload(file=f, path=nome_nuvem, file_options={"upsert": "true"})
        
    print("\n[+] CAMADA BRONZE ENVIADA PARA A NUVEM!")
    # Pega o link público para você mandar para o avaliador
    url_publica = supabase.storage.from_("bronze-storage").get_public_url(nome_nuvem)
    print(f"-> Link público para o avaliador: {url_publica}")

if __name__ == "__main__":
    subir_bronze_nuvem()
