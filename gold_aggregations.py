import pandas as pd
from sqlalchemy import create_engine


# CONFIGURAÇÃO DA NUVEM (SUPABASE)
DATABASE_URL = "postgresql://postgres:Projetomovida0826@db.dzzmtkevibrucyoywvho.supabase.co:5432/postgres"


def criar_camada_gold():
    print("[*] Conectando ao banco para ler a Camada Silver...")
    try:
        engine = create_engine(DATABASE_URL)
        df = pd.read_sql_table("veiculos_silver", engine)
        print(f"[+] {len(df)} carros lidos da nuvem.")

        print("[*] Calculando o TRM (Taxa de Rodagem Mensal)...")
        # Tratando a regra de negócio: Idade = 0 significa carro do semestre anterior 
        df['idade_para_trm'] = df['idade_anos'].apply(lambda x: 0.5 if x == 0 else x)
        
        # Cálculo do TRM: KM dividido pelos meses que o carro tem
        df['trm'] = (df['quilometragem'] / (df['idade_para_trm'] * 12)).round(0)

        print("[*] Criando agregações por Loja, Cidade e Estado (Camada Gold)...")
        # Agrupando por Loja
        df_gold = df.groupby(['estado', 'cidade', 'loja']).agg(
            total_veiculos=('id_carro', 'count'),
            preco_medio=('preco', 'mean'),
            km_media=('quilometragem', 'mean'),
            idade_media_anos=('idade_anos', 'mean'),
            trm_medio=('trm', 'mean') # O Novo KPI principal!
        ).reset_index()

        # Arredondando para o dashboard ficar mais limpo
        df_gold['preco_medio'] = df_gold['preco_medio'].round(2)
        df_gold['km_media'] = df_gold['km_media'].round(0)
        df_gold['idade_media_anos'] = df_gold['idade_media_anos'].round(1)
        df_gold['trm_medio'] = df_gold['trm_medio'].round(0)

        print(f"[+] Agregações concluídas. {len(df_gold)} lojas analisadas.")

        # Salvando na nuvem ouseja no Supabase
        print("[*] Enviando Camada Gold para o Supabase...")
        df_gold.to_sql("veiculos_gold", engine, if_exists="replace", index=False)
        
        print("\n[+] CAMADA GOLD CONCLUÍDA COM SUCESSO!")
        print("-> Tabela 'veiculos_gold' criada/atualizada no Supabase.")
        print("-> KPIs e TRM prontos para o Power BI!")

    except Exception as e:
        print(f"[!] Erro ao criar Camada Gold: {e}")

if __name__ == "__main__":
    criar_camada_gold()
