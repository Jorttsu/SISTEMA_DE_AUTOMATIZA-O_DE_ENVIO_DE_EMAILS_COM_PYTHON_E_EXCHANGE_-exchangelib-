'''
Script para iniciar a base de dados e importar as templates iniciais
'''
import os
import sys
from pathlib import Path

#Adicionar o diretório raiz ao path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from db.database import init_db
from email_automation.templates import importar_templates_para_db
from config import TEMPLATE_FILE

def main():
    print("=" * 60)
    print("INICIAR A BASE DE DADOS")
    print("=" * 60)
    
    try:
        #1.Iniciar a base de dados
        print("1. A criar tabelas da base de dados...")
        init_db()
        print("   :) : Tabelas criadas com sucesso")
        
        #2. Importar as templates se o documento existir
        if os.path.exists(TEMPLATE_FILE):
            print("2. A importar templates do documento Word...")
            count = importar_templates_para_db(TEMPLATE_FILE)
            print(f"   :) : {count} templates importadas")
        else:
            print("2. !:  Documento de templates não encontrado.")
        
        print("Iniciado com sucesso!")
        print("Agora pode executar o sistema normalmente.")
        
    except Exception as e:
        print(f"X: Erro durante a inicialização: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())