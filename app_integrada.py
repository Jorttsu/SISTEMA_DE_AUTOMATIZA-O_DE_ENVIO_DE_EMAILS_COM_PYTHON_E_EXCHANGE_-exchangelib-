import os
import sys
import time
import traceback
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import docx
import re
from exchangelib import Credentials, Account, Message, Mailbox, DELEGATE

# Importações dos módulos do projeto
from config import (
    LOG_DIR, TEMPLATE_FILE, EXCEL_FILE, RETRY_QUEUE_FILE,
    MAX_RETRY_ATTEMPTS, RETRY_INTERVAL, EMAIL_CONFIG_FILE,
    SQLALCHEMY_DATABASE_URI
)
from db.models import db, Log
from email_automation.email_sender import EmailSender
from email_retry_queue import EmailRetryQueue
from email_automation.templates import carregar_templates_docx
from destinatarios import carregar_destinatarios
from email_automation.email_task import EmailTask
from processar_template import processar_template
from credenciais import verificar_credenciais, configurar_credenciais

# Configuração da aplicação Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "supersecret_email_automation"
db.init_app(app)

class ExchangeLibEmailSender:
    """Classe responsável pelo envio de emails via Exchange (exchangelib)."""
    def __init__(self, logger=None, email=None, palavra_passe=None):
        self.logger = logger
        self.email = email
        self.palavra_passe = palavra_passe
        self.account = None

    def iniciar(self):
        try:
            self.logger.info("A iniciar ligação ao Exchange via exchangelib...")
            credentials = Credentials(self.email, self.palavra_passe)
            self.account = Account(
                primary_smtp_address=self.email,
                credentials=credentials,
                autodiscover=True,
                access_type=DELEGATE
            )
            _ = self.account.inbox.total_count
            self.logger.info("Ligação ao Exchange estabelecida com sucesso.")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao iniciar ligação ao Exchange: {e}")
            return False

    def enviar_email(self, destinatario, nome, assunto, corpo_mensagem, anexos=None, cc=None, bcc=None, html=None):
        if self.account is None and not self.iniciar():
            return False
        try:
            to_recipients = [Mailbox(email_address=destinatario)]
            cc_recipients = [Mailbox(email_address=addr) for addr in cc] if cc else []
            bcc_recipients = [Mailbox(email_address=addr) for addr in bcc] if bcc else []
            body_type = 'HTML' if (html or (corpo_mensagem and '<html>' in corpo_mensagem.lower())) else 'TEXT'
            m = Message(
                account=self.account,
                subject=assunto,
                body=corpo_mensagem,
                to_recipients=to_recipients,
                cc_recipients=cc_recipients,
                bcc_recipients=bcc_recipients
            )
            # Adicionar anexos se existirem (não implementado nesta versão)
            m.send()
            self.logger.info(f"Email enviado com sucesso para {destinatario}")
            time.sleep(0.5)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar email para {destinatario} via Exchange: {e}")
            return False

class IntegratedEmailSystem:
    def __init__(self):
        self.logger = None
        self.email_sender = None
        self.retry_queue = None
        self.templates = {}
        self.destinatarios = []
        self.is_running = False
        self.current_progress = 0
        self.total_emails = 0
        self.ready = False
        self.stats = {
            'emails_enviados': 0,
            'emails_falharam': 0,
            'emails_pendentes': 0,
            'tempo_inicio': None,
            'tempo_fim': None
        }
        self.use_selenium = False

    def configurar_logging(self):
        import logging
        logger = logging.getLogger("EmailAutomation")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(logs_dir, "email_automation.log"))
        file_handler.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger

    def iniciar_sistema(self):
        try:
            self.logger = self.configurar_logging()
            self.logger.info("A iniciar o sistema de automatização de emails")
            self.ready = False
            if not self._verificar_ficheiros_essenciais():
                return False, "Ficheiros essenciais em falta"
            if not self._carregar_templates():
                return False, "Erro ao carregar templates"
            if not self._carregar_destinatarios():
                return False, "Erro ao carregar lista de destinatários"
            if not self._iniciar_componentes_envio():
                return False, "Erro ao iniciar as componentes de envio"
            self.ready = True
            self.logger.info("Sistema iniciado com sucesso")
            return True, "Sistema iniciado com sucesso"
        except Exception as e:
            self.ready = False
            error_msg = f"Erro crítico ao iniciar: {e}"
            if self.logger:
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
            return False, error_msg

    def _verificar_ficheiros_essenciais(self):
        ficheiros_essenciais = [
            (TEMPLATE_FILE, "Ficheiro de templates"),
            (EXCEL_FILE, "Ficheiro de destinatários"),
        ]
        ficheiros_em_falta = []
        for ficheiro, descricao in ficheiros_essenciais:
            if not os.path.exists(ficheiro):
                ficheiros_em_falta.append((ficheiro, descricao))
        if ficheiros_em_falta:
            self.logger.error("Ficheiros essenciais em falta:")
            for ficheiro, descricao in ficheiros_em_falta:
                self.logger.error(f"  - {descricao}: {ficheiro}")
            return False
        return True

    def _carregar_templates(self):
        try:
            self.templates = self.carregar_templates_docx(TEMPLATE_FILE)
            if not self.templates:
                self.logger.error("Nenhuma template foi carregada")
                return False
            self.logger.info(f"Templates carregadas: {list(self.templates.keys())}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao carregar templates: {e}")
            return False

    def _carregar_destinatarios(self):
        try:
            self.destinatarios = carregar_destinatarios(EXCEL_FILE, self.logger)
            if not self.destinatarios:
                self.logger.error("Nenhum destinatário foi carregado")
                return False
            self.total_emails = len(self.destinatarios)
            self.logger.info(f"Destinatários carregados: {self.total_emails} total")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao carregar destinatários: {e}")
            return False

    def _iniciar_componentes_envio(self):
        try:
            credenciais = verificar_credenciais()
            if not credenciais or not credenciais.get('email') or not credenciais.get('palavra_passe'):
                self.logger.error("Credenciais de email não configuradas corretamente para Exchange.")
                flash("Credenciais de email não configuradas corretamente para Exchange. Certifique-se que preencheu o email e a palavra-passe na configuração.", 'error')
                return False
            self.email_sender = ExchangeLibEmailSender(
                logger=self.logger,
                email=credenciais['email'],
                palavra_passe=credenciais['palavra_passe']
            )
            if not self.email_sender.iniciar():
                self.logger.error("Falha ao iniciar o enviador de emails via Exchange. Verifique as credenciais.")
                flash("Falha ao iniciar o envio: Verifique as credenciais Exchange (email e palavra-passe corretos).", 'error')
                return False
            self.retry_queue = EmailRetryQueue(
                arquivo_fila=RETRY_QUEUE_FILE,
                max_tentativas=MAX_RETRY_ATTEMPTS,
                intervalo_tentativas=RETRY_INTERVAL,
                logger=self.logger
            )
            return True
        except Exception as e:
            self.logger.error(f"Erro ao iniciar componentes de envio: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            flash("Erro ao iniciar componentes de envio: " + str(e), 'error')
            return False

    def carregar_templates_docx(self, ficheiro):
        templates = {}
        if not os.path.exists(ficheiro):
            self.logger.error(f"Ficheiro de templates não encontrado: {ficheiro}")
            return templates
        try:
            doc = docx.Document(ficheiro)
            texto_completo = ""
            for paragrafo in doc.paragraphs:
                texto_completo += paragrafo.text + "\n"
            padrao_template = r'###\s*(\w+)\s*###\s*\n(.*?)(?=\n###|\Z)|###(\w+)###\s*\n(.*?)(?=\n###|\Z)'
            matches = re.findall(padrao_template, texto_completo, re.DOTALL)
            for m in matches:
                nome = m[0] if m[0] else m[2]
                conteudo = m[1] if m[1] else m[3]
                templates[nome.strip().lower()] = conteudo.strip()
            self.logger.info(f"Carregados {len(templates)} templates")
            return templates
        except Exception as e:
            self.logger.error(f"Erro ao carregar templates: {e}")
            return {}

    def iniciar_envio_automatico(self):
        if not self.ready:
            return False, "O sistema não foi iniciado corretamente."
        if self.is_running:
            return False, "O envio já está em execução"
        self.stats = {
            'emails_enviados': 0,
            'emails_falharam': 0,
            'emails_pendentes': 0,
            'tempo_inicio': datetime.now(),
            'tempo_fim': None
        }
        self.current_progress = 0
        self.is_running = True
        thread = threading.Thread(target=self._processar_emails_thread)
        thread.daemon = True
        thread.start()
        return True, "Envio automático iniciado"

    def _processar_emails_thread(self):
        try:
            self.logger.info(f"A iniciar o envio de {self.total_emails} emails")
            for indice, destinatario in enumerate(self.destinatarios, 1):
                if not self.is_running:
                    break
                try:
                    self.current_progress = indice
                    self._processar_email_individual(destinatario, indice)
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Erro ao processar email {indice}: {e}")
                    self.stats['emails_falharam'] += 1
            self.stats['tempo_fim'] = datetime.now()
        except Exception as e:
            self.logger.error(f"Erro crítico no envio automático: {e}")
        finally:
            self.is_running = False
            self.current_progress = self.total_emails
            self.logger.info("Envio automático concluído")
            with app.app_context():
                db.session.commit()
            time.sleep(0.5)

    def _processar_email_individual(self, destinatario, indice):
        template_nome = destinatario.get('template', '').lower().strip()
        nome = destinatario.get('nome', 'Destinatário').strip()
        email = destinatario.get('email', '').strip()
        assunto = destinatario.get('assunto', 'Sem assunto').strip()
        if not email or '@' not in email:
            self.logger.warning(f"Email inválido para {nome}: '{email}'")
            self.stats['emails_falharam'] += 1
            with app.app_context():
                db.session.add(Log(email=email, action='falha', detail='Email inválido'))
                db.session.commit()
            return
        if not template_nome or template_nome not in self.templates:
            self.logger.warning(f"Template '{template_nome}' não encontrada para {nome}")
            self.stats['emails_falharam'] += 1
            with app.app_context():
                db.session.add(Log(email=email, action='falha', detail=f'Template "{template_nome}" não encontrado'))
                db.session.commit()
            return
        template_corpo = self.templates.get(template_nome)
        corpo_email = processar_template(template_corpo, {
            'nome': nome,
            'email': email,
            'assunto': assunto
        })
        if not corpo_email:
            self.logger.warning(f"Falha ao processar a template para {nome}")
            self.stats['emails_falharam'] += 1
            with app.app_context():
                db.session.add(Log(email=email, action='falha', detail='Erro na ação de processamento da template'))
                db.session.commit()
            return
        sucesso = self.email_sender.enviar_email(
            destinatario=email,
            nome=nome,
            assunto=assunto,
            corpo_mensagem=corpo_email
        )
        with app.app_context():
            if sucesso:
                self.logger.info(f"Email enviado para {nome} ({email})")
                self.stats['emails_enviados'] += 1
                db.session.add(Log(email=email, action='enviado', detail=f'Enviado para {nome}'))
            else:
                self.logger.warning(f"Falha ao enviar para {nome} ({email})")
                self.stats['emails_falharam'] += 1
                db.session.add(Log(email=email, action='falha', detail='Erro no envio'))
                email_task = EmailTask(
                    destinatario=email,
                    nome=nome,
                    assunto=assunto,
                    corpo_mensagem=corpo_email,
                    template_used=template_nome
                )
                self.retry_queue.adicionar_email(email_task)
                self.stats['emails_pendentes'] += 1
            db.session.commit()

    def parar_envio(self):
        self.is_running = False
        return True, "O envio foi interrompido"

    def get_progress(self):
        return {
            'is_running': self.is_running,
            'current': self.current_progress,
            'total': self.total_emails,
            'stats': self.stats.copy(),
            'ready': self.ready
        }

email_system = IntegratedEmailSystem()

@app.before_request
def create_tables():
    db.create_all()

@app.route('/')
def dashboard():
    try:
        logs = Log.query.order_by(Log.timestamp.desc()).limit(100).all()
        total_logs = Log.query.count()
        total_envios = Log.query.filter_by(action='enviado').count()
        total_falhas = Log.query.filter_by(action='falha').count()
        system_status = email_system.get_progress()
        credenciais = verificar_credenciais()
        email_configurado = credenciais['email'] if credenciais and 'email' in credenciais else None
        return render_template(
            'dashboard.html',
            logs=logs,
            total_logs=total_logs,
            total_envios=total_envios,
            total_falhas=total_falhas,
            system_status=system_status,
            email_configurado=email_configurado
        )
    except Exception as e:
        flash(f"Erro ao carregar dashboard: {e}", 'error')
        return render_template('dashboard.html', logs=[], total_logs=0, total_envios=0, total_falhas=0, system_status={'is_running': False})

@app.route('/inicializar-sistema', methods=['POST'])
def inicializar_sistema():
    try:
        sucesso, mensagem = email_system.iniciar_sistema()
        if sucesso:
            flash(mensagem, 'success')
        else:
            flash(mensagem, 'error')
    except Exception as e:
        flash(f"Erro ao iniciar sistema: {e}", 'error')
    return redirect(url_for('dashboard'))

@app.route('/iniciar-envio', methods=['POST'])
def iniciar_envio():
    try:
        sucesso, mensagem = email_system.iniciar_envio_automatico()
        if sucesso:
            flash(mensagem, 'success')
        else:
            flash(mensagem, 'warning')
    except Exception as e:
        flash(f"Erro ao iniciar envio: {e}", 'error')
    return redirect(url_for('dashboard'))

@app.route('/parar-envio', methods=['POST'])
def parar_envio():
    try:
        sucesso, mensagem = email_system.parar_envio()
        if sucesso:
            flash(mensagem, 'info')
        else:
            flash(mensagem, 'error')
    except Exception as e:
        flash(f"Erro ao parar envio: {e}", 'error')
    return redirect(url_for('dashboard'))

@app.route('/api/progress')
def api_progress():
    return jsonify(email_system.get_progress())

@app.route('/api/logs')
def api_logs():
    try:
        logs = Log.query.order_by(Log.timestamp.desc()).limit(50).all()
        logs_data = [{
            'id': log.id,
            'timestamp': log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'email': log.email,
            'action': log.action,
            'detail': log.detail
        } for log in logs]
        return jsonify(logs_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def remover_credenciais():
    config_file = EMAIL_CONFIG_FILE if 'EMAIL_CONFIG_FILE' in globals() else 'email_config.json'
    try:
        if os.path.exists(config_file):
            os.remove(config_file)
        try:
            import keyring
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
            if 'email' in config:
                keyring.delete_password("outlook_automation", config['email'])
        except Exception:
            pass
        return True
    except Exception as e:
        return False

@app.route('/remover-credenciais', methods=['POST'])
def remover_credenciais_web():
    try:
        if remover_credenciais():
            flash('Credenciais removidas com sucesso!', 'success')
        else:
            flash('Erro ao remover credenciais.', 'error')
    except Exception as e:
        flash(f'Erro ao remover credenciais: {e}', 'error')
    return redirect(url_for('configurar_credenciais_web'))

@app.route('/configurar-credenciais', methods=['GET', 'POST'])
def configurar_credenciais_web():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            usar_windows = request.form.get('usar_windows') == 'on'
            senha = request.form.get('senha') if not usar_windows else None
            if not email or '@' not in email:
                flash('Email inválido', 'error')
                return render_template('configurar_credenciais.html')
            configurar_credenciais(email, usar_windows, senha)
            flash('Credenciais configuradas com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Erro ao configurar as credenciais: {e}', 'error')
    return render_template('configurar_credenciais.html')

@app.route('/limpar-logs', methods=['POST'])
def limpar_logs():
    try:
        Log.query.delete()
        db.session.commit()
        flash('Logs limpos com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao limpar os logs: {e}', 'error')
    return redirect(url_for('dashboard'))

@app.route('/log/<int:log_id>')
def log_detail(log_id):
    log = Log.query.get_or_404(log_id)
    return render_template('log_detail.html', log=log)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("=" * 60)
    print("SISTEMA INTEGRADO DE AUTOMATIZAÇÃO DE EMAILS")
    print("Dashboard Web + Envio Automático")
    print("=" * 60)
    print("Acesse: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)