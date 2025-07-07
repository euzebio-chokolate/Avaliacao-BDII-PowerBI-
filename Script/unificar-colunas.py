import pandas as pd

def juntar_todas_as_traducoes_dos_finais(original_csv='athlete_events.csv', output_csv='eventos_atletas.csv'):
    
    print(f"Carregando o arquivo original: {original_csv}")
    try:
        # Este será o DataFrame onde todas as traduções serão consolidadas
        df_consolidado = pd.read_csv(original_csv) 
    except FileNotFoundError:
        print(f"Erro: O arquivo '{original_csv}' não foi encontrado. Verifique o caminho.")
        return
    
    # Lista das colunas que esperamos ter arquivos _final.csv traduzidos
    colunas_com_finais_traduzidos = ['Event', 'Sport', 'Team', 'City']
    
    for coluna in colunas_com_finais_traduzidos:
        # Nome do arquivo _final.csv para a coluna atual
        final_csv_filename = f'traduzido_deepl_{coluna.lower()}_final.csv'
        
        print(f"\nTentando carregar o arquivo final traduzido para a coluna '{coluna}' de '{final_csv_filename}'...")
        try:
            df_col_traduzida = pd.read_csv(final_csv_filename)
            
            # Verificar se a coluna existe no DataFrame traduzido
            if coluna in df_col_traduzida.columns:
                # Copia a coluna traduzida do arquivo _final.csv para o DataFrame principal consolidado.
                # Isso assume que os DataFrames têm o mesmo número de linhas e ordem das linhas.
                df_consolidado[coluna] = df_col_traduzida[coluna]
                print(f"Coluna '{coluna}' traduzida aplicada com sucesso.")
            else:
                print(f"Aviso: A coluna '{coluna}' não foi encontrada em '{final_csv_filename}'. Pulando a atualização para esta coluna.")
                
        except FileNotFoundError:
            print(f"Aviso: Arquivo '{final_csv_filename}' não encontrado. A coluna '{coluna}' permanecerá no idioma original.")
        except Exception as e:
            print(f"Erro ao aplicar traduções para a coluna '{coluna}' de '{final_csv_filename}': {e}")
            
    print(f"\nTodas as traduções disponíveis aplicadas. Salvando o arquivo final em '{output_csv}'...")
    df_consolidado.to_csv(output_csv, index=False)
    print("Processo concluído!")

# --- Executa a função para juntar as traduções ---
juntar_todas_as_traducoes_dos_finais()