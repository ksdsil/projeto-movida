import requests
import json
import time
import os

# URL da API oculta da Movida
API_URL = "https://be-seminovos.movidacloud.com.br/elasticsearch/veiculos"

# Headers simulando um navegador real (pra não ser bloqueado)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.seminovosmovida.com.br",
    "Referer": "https://www.seminovosmovida.com.br/"
}

def coletar_veiculos():
    print("[*] Iniciando coleta de dados via API (Camada Bronze)...")
    todos_veiculos = []
    offset = 0  # O payload inicial é {"from": null}, que é equivale a 0
    
    while True:
        # Monta o payload pra paginação
        payload = {"from": offset}
        
        try:
            # Faz a requisição POST para a API
            response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
            response.raise_for_status()
            
            dados = response.json()
            lista_carros = dados.get("data", [])
            total_carros = dados.get("total", {}).get("value", 0)
            
            if not lista_carros:
                print("[!] Nenhum veículo encontrado nesta página. Fim da coleta.")
                break
                
            # Adiciona os carros da página atual na lista geral
            todos_veiculos.extend(lista_carros)
            print(f"[+] Coletados {len(todos_veiculos)} de {total_carros} veículos...")
            
            # Atualiza o offset para a próxima página (os próxims 20 carros)
            offset += len(lista_carros)
            
            # Condição de parada: se já pegamos todos os carros
            if len(todos_veiculos) >= total_carros:
                print("[*] Todos os veículos foram coletados com sucesso!")
                break
                
            # Pausa de 0.5s pra não bombardear o servidor 
            time.sleep(0.5)
            
        except requests.exceptions.RequestException as e:
            print(f"[!] Erro durante a requisição: {e}")
            break

    return todos_veiculos

def salvar_camada_bronze(veiculos):
    if not veiculos:
        print("[!] Nenhum dado para salvar.")
        return

    # Cria a pasta 'bronze' se ela não existir
    pasta_bronze = "bronze"
    os.makedirs(pasta_bronze, exist_ok=True)
    
    # Nome do arquivo com tmestamp para histórico
    nome_arquivo = os.path.join(pasta_bronze, "veiculos_raw.json")
    
    # Salva os dados brutos
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(veiculos, f, ensure_ascii=False, indent=4)
        
    print(f"\n[+] CAMADA BRONZE CONCLUÍDA!")
    print(f"-> Arquivo salvo em: {nome_arquivo}")
    print(f"-> Total de registros: {len(veiculos)}")

if __name__ == "__main__":
    dados_coletados = coletar_veiculos()
    salvar_camada_bronze(dados_coletados)
