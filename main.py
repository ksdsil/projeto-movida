import os
import requests
import json
import csv
import time
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega variáveis de ambiente (funciona no Linux local e no GitHub Actions)
load_dotenv()

# Pega as credenciais do ambiente (seguro pra subir no GitHub)
API_URL = "https://be-seminovos.movidacloud.com.br/elasticsearch/veiculos"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.seminovosmovida.com.br",
    "Referer": "https://www.seminovosmovida.com.br/"
}

DB_URL = os.environ.get("DB_URL")
SUPA_URL = os.environ.get("SUPA_URL")
SUPA_KEY = os.environ.get("SUPA_KEY")

def coletar_dados():
    print("[1/5] Coletando dados via API...")
    todos_veiculos = []
    offset = 0
    while True:
        payload = {"from": offset}
        response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
        response.raise_for_status()
        dados = response.json()
        lista_carros = dados.get("data", [])
        total_carros = dados.get("total", {}).get("value", 0)
        if not lista_carros: break
        todos_veiculos.extend(lista_carros)
        offset += len(lista_carros)
        if len(todos_veiculos) >= total_carros: break
        time.sleep(0.5)
    
    # Salva Bronze Localmente
    os.makedirs("bronze", exist_ok=True)
    with open("bronze/veiculos_raw.json", "w", encoding="utf-8") as f:
        json.dump(todos_veiculos, f, ensure_ascii=False, indent=4)
    print(f"-> Bronze local salva. Total: {len(todos_veiculos)} carros.")
    return todos_veiculos

def transformar_dados(dados_brutos):
    print("[2/5] Transformando dados (Silver)...")
    from datetime import datetime
    ano_atual = datetime.now().year
    veiculos_limpos = []
    for carro in dados_brutos:
        ano_modelo = int(carro.get("ano_modelo", ano_atual))
        idade = ano_atual - ano_modelo
        idade_tratada = 0.5 if idade == 0 else idade
        trm = round(int(carro.get("quilometragem", 0)) / (idade_tratada * 12))
        
        veiculos_limpos.append({
            "id_carro": carro.get("id"),
            "marca": carro.get("marca", "NI"),
            "modelo": carro.get("modelo", "NI"),
            "versao": carro.get("versao", "NI"),
            "cor": carro.get("cor", "NI"),
            "ano_fabricacao": ano_modelo,
            "quilometragem": int(carro.get("quilometragem", 0)),
            "idade_anos": idade,
            "trm": int(trm) if trm == trm else 0,# Nosso KPI autoral incluído direto no Silver!
            "preco": float(carro.get("preco", 0.0)),
            "valor_parcela": float(carro.get("financiamento", {}).get("valor_parcela", 0.0)),
            "loja": carro.get("loja", "NI"),
            "cidade": carro.get("cidade", "NI"),
            "estado": carro.get("uf", "NI")
        })
    
    os.makedirs("silver", exist_ok=True)
    with open("silver/veiculos_clean.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(veiculos_limpos[0].keys()))
        writer.writeheader()
        writer.writerows(veiculos_limpos)
    print("-> Silver local salva (CSV).")
    return veiculos_limpos

def carregar_nuvem(dados_limpos):
    print("[3/5] Enviando Silver para Supabase...")
    df = pd.DataFrame(dados_limpos)
    engine = create_engine(DB_URL)
    df.to_sql("veiculos_silver", engine, if_exists="replace", index=False)
    print("-> Tabela 'veiculos_silver' atualizada na nuvem!")

def criar_gold():
    print("[4/5] Criando Gold (Agregações)...")
    engine = create_engine(DB_URL)
    df = pd.read_sql_table("veiculos_silver", engine)
    
    df_gold = df.groupby(['estado', 'cidade', 'loja']).agg(
        total_veiculos=('id_carro', 'count'),
        preco_medio=('preco', 'mean'),
        km_media=('quilometragem', 'mean'),
        idade_media_anos=('idade_anos', 'mean'),
        trm_medio=('trm', 'mean')
    ).reset_index()

    df_gold['preco_medio'] = df_gold['preco_medio'].round(2)
    df_gold['km_media'] = df_gold['km_media'].round(0)
    df_gold['idade_media_anos'] = df_gold['idade_media_anos'].round(1)
    df_gold['trm_medio'] = df_gold['trm_medio'].round(0)

    df_gold.to_sql("veiculos_gold", engine, if_exists="replace", index=False)
    print("-> Tabela 'veiculos_gold' atualizada na nuvem!")

def subir_bronze_nuvem():
    print("[5/5] Subindo Bronze para Supabase Storage...")
    supabase: Client = create_client(SUPA_URL, SUPA_KEY)
    with open("bronze/veiculos_raw.json", "rb") as f:
        supabase.storage.from_("bronze-storage").upload(file=f, path="veiculos_raw.json", file_options={"upsert": "true"})
    print("-> Bronze atualizada na nuvem!")

if __name__ == "__main__":
    print("=== INICIANDO PIPELINE DE DADOS MOVIDA ===")
    bronze = coletar_dados()
    silver = transformar_dados(bronze)
    carregar_nuvem(silver)
    criar_gold()
    subir_bronze_nuvem()
    print("=== PIPELINE CONCLUÍDO COM SUCESSO! ===")
