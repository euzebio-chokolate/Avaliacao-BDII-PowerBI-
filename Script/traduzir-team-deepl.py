import pandas as pd
import deepl
import time
import os
import re

DEEPL_API_KEY = "37ddaf4d-0816-4616-91e4-593f4d0ef0db:fx" # Trocar depois para variável de ambiente
translator = deepl.Translator(DEEPL_API_KEY)

# --- Funções Auxiliares ---
def save_progress(df_to_save, filename='traduzido_deepl_team_cache.csv'):
    """Salva o DataFrame atual em um arquivo CSV."""
    df_to_save.to_csv(filename, index=False)
    print(f"\nProgresso salvo em '{filename}'.")

def traduzir_com_deepl(texto):
    """
    Função para traduzir texto usando a API do DeepL.
    Adiciona um prompt específico e tenta extrair apenas a tradução.
    """
    if pd.isna(texto) or texto.strip() == "":
        return texto # Retorna o próprio valor se for NaN ou vazio

    try:
        result = translator.translate_text(
            texto,
            target_lang='pt-BR'
        )
        
        traducao_final = result.text.strip()
        return traducao_final
    except deepl.exceptions.QuotaExceededException as e:
        # Erro específico do DeepL para cota excedida
        raise Exception("Quota Exceeded (DeepL)")
    except deepl.exceptions.TooManyRequestsException as e:
        # Erro específico do DeepL para muitas requisições (rate limit)
        print(f"Alerta DeepL: Muitas requisições. Erro: {e}")
        raise Exception("Too Many Requests (DeepL)")
    except deepl.exceptions.DeepLException as e:
        print(f"Erro específico do DeepL ao traduzir '{texto}': {e}")
        return texto
    except Exception as e:
        print(f"Erro inesperado ao traduzir '{texto}': {e}")
        return texto

# --- Carregar dados ---
try:
    df = pd.read_csv('athlete_events.csv')
except FileNotFoundError:
    print("Erro: O arquivo 'athlete_events.csv' não foi encontrado. Por favor, verifique o caminho.")
    exit()

coluna = 'Team'

# Carregar o DataFrame traduzido se ele já existir para continuar o trabalho
try:
    df_traduzido_parcial = pd.read_csv('traduzido_deepl_team_cache.csv')
    print("Arquivo 'traduzido_deepl_team_cache.csv' encontrado. Carregando progresso anterior...")
    
    if 'Team_Original' in df_traduzido_parcial.columns and 'Team' in df_traduzido_parcial.columns:
        cache = df_traduzido_parcial.set_index('Team_Original')['Team'].dropna().to_dict()
    else:
        print("Aviso: 'traduzido_deepl_team_cache.csv' não tem as colunas 'Team_Original' e 'Team'. Reconstruindo cache.")
        cache = {}
        
    # Salva o valor original da coluna 'Team' antes de aplicar as traduções
    df['Team_Original'] = df['Team'] 
    df['Team'] = df['Team'].map(cache).fillna(df['Team_Original'])

    # Para identificar os valores originais que precisam de tradução, é melhor ler do arquivo original
    valores_unicos_originais = pd.read_csv('athlete_events.csv')[coluna].dropna().unique()
    valores_para_traduzir = [v for v in valores_unicos_originais if v not in cache]
    print(f"Foram encontradas {len(cache)} traduções no cache para 'Team'. Restam {len(valores_para_traduzir)} para traduzir.")

except FileNotFoundError:
    print("Arquivo 'traduzido_deepl_team_cache.csv' não encontrado. Iniciando tradução do zero para 'Team'.")
    cache = {}
    valores_unicos_originais = df[coluna].dropna().unique()
    valores_para_traduzir = valores_unicos_originais.tolist()
    df['Team_Original'] = df['Team'] # Cria a coluna Team_Original para o caso de iniciar do zero

print(f"\nIniciando/Continuando tradução de {len(valores_para_traduzir)} equipes com DeepL...")

total_equipes_processadas_sessao = 0
try:
    for i, texto_original in enumerate(valores_para_traduzir):
        if texto_original in cache:
            continue

        traduzido = traduzir_com_deepl(texto_original)
        cache[texto_original] = traduzido
        total_equipes_processadas_sessao += 1
        print(f'{i+1}/{len(valores_para_traduzir)}: {texto_original} → {traduzido}')
        
        time.sleep(0.1) # Pausa para evitar rate limits

except Exception as e:
    if str(e) == "Quota Exceeded (DeepL)":
        print("\n--- Limite de Cota da API do DeepL excedido para 'Team'! ---")
        print("Você atingiu o limite mensal de caracteres do DeepL API Free.")
        print("Progresso salvo. Por favor, aguarde o reset mensal ou considere um plano pago.")
    elif str(e) == "Too Many Requests (DeepL)":
        print("\n--- Alerta DeepL: Muitas requisições em um curto período para 'Team'! ---")
        print("O DeepL pode ter acionado um rate limit temporário. Tente novamente em alguns segundos/minutos.")
        print("Aumente o `time.sleep()` se este erro persistir.")
    else:
        print(f"\n--- Ocorreu um erro inesperado: {e} ---")
    
    # Salva o progresso antes de sair em ambos os casos de erro
    df_temp_salvar = pd.DataFrame(list(cache.items()), columns=['Team_Original', 'Team'])
    save_progress(df_temp_salvar, 'traduzido_deepl_team_cache.csv')
    exit()

print(f"\nTradução em cache concluída para {total_equipes_processadas_sessao} novas equipes nesta sessão.")

# Criar um novo DataFrame com os valores únicos e suas traduções para facilitar o mapeamento
df_traducoes_completas = pd.DataFrame(list(cache.items()), columns=['Team_Original', 'Team_Traduzido'])

# Aplica as traduções baseadas na coluna 'Team_Original'
# Certifique-se de que df['Team_Original'] existe antes desta linha
df['Team'] = df['Team_Original'].map(df_traducoes_completas.set_index('Team_Original')['Team_Traduzido']).fillna(df['Team_Original'])

# Remove a coluna Team_Original se não for mais necessária para o CSV final
df.drop(columns=['Team_Original'], inplace=True)

# Salva o DataFrame final traduzido (nome diferente para não sobrescrever o cache de progresso)
save_progress(df, 'traduzido_deepl_team_final.csv')
print('\nTradução de todas as equipes concluída e salva em traduzido_deepl_team_final.csv.')
