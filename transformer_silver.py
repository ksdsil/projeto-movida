import json
import csv
import os
from datetime import datetime

def carregar_dados_bronze():
    caminho_bronze = "bronze/veiculos_raw.json"
    if not os.path.exists(caminho_bronze):
        print("[!] Arquivo da Camada Bronze não encontrado. Rode o scraper primeiro.")
        return None
    with open(caminho_bronze, "r", encoding="utf-8") as f:
        return json.load(f)

def transformar_para_silver(dados_brutos):
    print("[*] Iniciando transformação de dados (Camada Silver)...")
    veiculos_limpos = []
    
    # Ano atual para calcular a idade do veículo (para o Coeficiente de Replacement)
    ano_atual = datetime.now().year

    for carro in dados_brutos:
        # Extrai e limpa os dados do JSON bruto
        try:
            # Cálculo da idade aproximada em anos
            ano_modelo = int(carro.get("ano_modelo", ano_atual))
            idade_veiculo = ano_atual - ano_modelo
            
            # Coleta da loja exata 
            loja = carro.get("loja", "Não Informado")
            cidade = carro.get("cidade", "Não Informado")
            uf = carro.get("uf", "NI")
            
            # Dados financeiros
            preco = float(carro.get("preco", 0.0))
            financiamento = carro.get("financiamento", {})
            valor_parcela = float(financiamento.get("valor_parcela", 0.0))
            valor_entrada = float(financiamento.get("valor_entrada", 0.0))
            
            # Dados do veículo
            registro = {
                "id_carro": carro.get("id"),
                "marca": carro.get("marca", "NI"),
                "modelo": carro.get("modelo", "NI"),
                "versao": carro.get("versao", "NI"),
                "cor": carro.get("cor", "NI"),
                "ano_fabricacao": ano_modelo,
                "quilometragem": int(carro.get("quilometragem", 0)),
                "idade_anos": idade_veiculo,
                "preco": preco,
                "valor_parcela": valor_parcela,
                "valor_entrada": valor_entrada,
                "loja": loja,
                "cidade": cidade,
                "estado": uf
            }
            veiculos_limpos.append(registro)
        except Exception as e:
            # Se um carro específico falhar, ignoramos e continuamos para não quebrar o lote
            print(f"[!] Erro ao processar carro ID {carro.get('id')}: {e}")
            continue

    return veiculos_limpos

def salvar_camada_silver(veiculos):
    if not veiculos:
        print("[!] Nenhum dado para salvar na Camada Silver.")
        return

    pasta_silver = "silver"
    os.makedirs(pasta_silver, exist_ok=True)
    nome_arquivo = os.path.join(pasta_silver, "veiculos_clean.csv")
    
    # Pega as chaves do dicionário para usar como cabeçalho do CSV
    cabecalho = list(veiculos[0].keys())
    
    with open(nome_arquivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cabecalho)
        writer.writeheader()
        writer.writerows(veiculos)
        
    print(f"\n[+] CAMADA SILVER CONCLUÍDA!")
    print(f"-> Arquivo salvo em: {nome_arquivo}")
    print(f"-> Total de registros limpos: {len(veiculos)}")

if __name__ == "__main__":
    dados_brutos = carregar_dados_bronze()
    if dados_brutos:
        dados_limpos = transformar_para_silver(dados_brutos)
        salvar_camada_silver(dados_limpos)
