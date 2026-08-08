import pandas as pd
from sqlalchemy import create_engine
import os

# ==========================================
# CONFIGURAÇÃO DA NUVEM (SUPABASE)
# Cole aqui a sua String de Conexão do Supabase
DATABASE_URL = os.environ.get("DB_URL")
# ==========================================

def carregar_csv_silver():
    caminho_csv = "silver/veiculos_clean.csv"
    if not os.path.exists(caminho_csv):
        print("[!] Arquivo CSV da camada silver não encontrado.")
        return None
    # O pandas é a forma mais pythônica e eficiente de ler e inserir dados em massa
    df = pd.read_csv(caminho_csv)
    print(f"[*] CSV carregado. {len(df)} registros prontos para a nuvem.")
    return df

def enviar_para_nuvem(df):
    if df is None:
        return

    print("[*] Conectando ao banco de dados na nuvem (Supabase)...")
    try:
        # Cria o motor de conexão do SQLAlchemy
        engine = create_engine(DATABASE_URL)
        
        print("[*] Enviando dados para a tabela 'veiculos_silver'...")
        # Envia o dataframe inteiro para o SQL. Se a tabela existir, ela será substituída.
        df.to_sql("veiculos_silver", engine, if_exists="replace", index=False)
        
        print("\n[+] DADOS ENVIADOS PARA A NUVEM COM SUCESSO!")
        print("-> Tabela 'veiculos_silver' criada no Supabase.")
    except Exception as e:
        print(f"[!] Erro ao conectar ou enviar dados: {e}")

if __name__ == "__main__":
    df_veiculos = carregar_csv_silver()
    enviar_para_nuvem(df_veiculos)
