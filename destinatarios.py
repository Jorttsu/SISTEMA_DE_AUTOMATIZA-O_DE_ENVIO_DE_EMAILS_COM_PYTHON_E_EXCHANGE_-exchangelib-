import pandas as pd
import logging
import traceback

def carregar_destinatarios(ficheiro, logger):
    try:
        #Usar encoding e tratar possíveis problemas
        df = pd.read_excel(ficheiro, dtype=str)  #Converter tudo para string
        
        #Tornar padrão os nomes das colunas (remover espaços, converter para minúsculas)
        df.columns = [col.lower().strip() for col in df.columns]
        
        #Verificar as colunas obrigatórias (case-insensitive)
        colunas_obrigatorias = ['nome', 'email', 'assunto', 'template']
        for coluna in colunas_obrigatorias:
            if coluna not in df.columns:
                logger.error(f"Coluna obrigatória '{coluna}' não encontrada no ficheiro Excel")
                raise ValueError(f"Coluna '{coluna}' não encontrada no ficheiro Excel")
        
        #Converter para uma lista de dicionários, garantindo os nomes das colunas em minúsculas
        destinatarios = df.to_dict('records')
        #Garantir que todos os campos obrigatórios existem em cada destinatário
        for d in destinatarios:
            for coluna in ['nome', 'email', 'assunto', 'template']:
                if coluna not in d:
                    d[coluna] = ''
        logger.info(f"Carregados {len(destinatarios)} destinatários")
        return destinatarios
    
    except Exception as e:
        logger.error(f"Erro ao carregar destinatários: {e}")
        #Imprimir traceback para diagnóstico
        logger.error(traceback.format_exc())
        return []