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

----------------
English Version:
----------------

===============================================================================
AUTOMATED EMAIL SENDING SYSTEM WITH PYTHON AND EXCHANGE (exchangelib)
===============================================================================

This project enables the automatic sending of personalized emails, using Word templates and an Excel recipient list, through a simple web interface.

----------------------
MAIN REQUIREMENTS
----------------------
- Python 3.8 or superior
- Install the project dependencies (see below)
- Exchange/Office 365 E-mail Account (with access EWS/Exchange Web Services)
- Files: destinatarios.xlsx (recipient list, Excel format) and Templates.docx (email templates, Word format)

---------------------------
INSTALLATION AND EXECUTION
---------------------------
1. Install the dependencies:
   pip install -r requirements.txt

2. Make sure that the 'destinatarios.xlsx' and 'Templates.docx' files are in the same folder as the project.

3. Run the application:
   python app_integrada.py

4. Open the browser and access:
   http://localhost:5000

---------
FEATURES
---------
- Configuration of Exchange email credentials via web page.
- Automatic loading of Word templates and Excel recipients.
- Automatic sending of personalized emails to each recipient via Exchange.
- Viewing of logs and system status in real time.
- Ability to clear logs and remove credentials.
- Support for automatic resending of failed emails.

----------------
iMPORTANT NOTES
----------------
- For sending via Exchange/Office 365, you may need to create an application password if the account has two-factor authentication (2FA).
- The account must have access to active Exchange Web Services (EWS). If you cannot authenticate, contact your institution's administrator.
- All logs are saved in the 'logs/' folder.

--------------------
CONTACT AND SUPPORT
--------------------
If you have any questions or problems, contact the project manager or use the support email address provided in the footer of the web application.
