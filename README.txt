===============================================================================
SISTEMA DE AUTOMATIZAÇÃO DE ENVIO DE EMAILS COM PYTHON E EXCHANGE (exchangelib)
===============================================================================

Este projeto permite o envio automático de emails personalizados, utilizando templates em formato Word e uma lista de destinatários em formato Excel, através de uma interface web simples.

----------------------
REQUISITOS PRINCIPAIS
----------------------
- Python 3.8 ou superior
- Instalar as dependências do projeto (ver abaixo)
- Conta de email Exchange/Office 365 (com acesso EWS/Exchange Web Services)
- Ficheiros: destinatarios.xlsx (lista de destinatários, formato Excel) e Templates.docx (templates de email, formato Word)

----------------------
INSTALAÇÃO E EXECUÇÃO
----------------------
1. Instale as dependências:
   pip install -r requirements.txt

2. Certifique-se de que os ficheiros 'destinatarios.xlsx' e 'Templates.docx' estão na mesma pasta do projeto.

3. Execute a aplicação:
   python app_integrada.py

4. Abra o browser e aceda a:
   http://localhost:5000

----------------------
FUNCIONALIDADES
----------------------
- Configuração de credenciais de email Exchange via página web.
- Carregamento automático de templates Word e destinatários Excel.
- Envio automático de emails personalizados para cada destinatário via Exchange.
- Visualização de logs e estado do sistema em tempo real.
- Possibilidade de limpar logs e remover credenciais.
- Suporte a reenvio automático de emails falhados.

----------------------
NOTAS IMPORTANTES
----------------------
- Para o envio via Exchange/Office 365, pode ser necessário criar uma palavra-passe de aplicação se a conta possuir uma autenticação de dois fatores (2FA).
- A conta deve ter acesso ao Exchange Web Services (EWS) ativo. Se não conseguir autenticar, contacte o administrador da sua instituição.
- Todos os logs são guardados na pasta 'logs/'.

----------------------
CONTACTO E SUPORTE
----------------------
Em caso de dúvidas ou problemas, contacte o responsável do projeto ou utilize o email de suporte indicado no rodapé da aplicação web.
