import os
import time
import pickle
import logging
import threading
from queue import Queue

from config import RETRY_QUEUE_FILE

class EmailRetryQueue:
    """Fila de emails pendentes para reenvio."""
    def __init__(self, arquivo_fila=RETRY_QUEUE_FILE, max_tentativas=3, 
                 intervalo_tentativas=300, logger=None):
        self.arquivo_fila = arquivo_fila
        self.max_tentativas = max_tentativas
        self.intervalo_tentativas = intervalo_tentativas
        self.logger = logger or logging.getLogger(__name__)
        self.fila = Queue()
        self.carregando = False
        self.running = False
        self.thread = None
        
        #Carregar a fila de emails pendentes do arquivo
        self.carregar_fila()
    
    def carregar_fila(self):
        """Carrega a fila de emails pendentes do documento."""
        self.carregando = True
        if os.path.exists(self.arquivo_fila):
            try:
                with open(self.arquivo_fila, 'rb') as f:
                    emails_pendentes = pickle.load(f)
                    for email in emails_pendentes:
                        self.fila.put(email)
                self.logger.info(f"Carregados {self.fila.qsize()} emails pendentes")
            except Exception as e:
                self.logger.error(f"Erro ao carregar emails pendentes: {e}")
        self.carregando = False
    
    def salvar_fila(self):
        """Guarda a fila de emails pendentes no documento."""
        if self.carregando:
            return
            
        emails_pendentes = []
        temp_fila = Queue()
        
        #Extração dos emails da fila
        while not self.fila.empty():
            email = self.fila.get()
            emails_pendentes.append(email)
            temp_fila.put(email)
        
        #Restaurar a fila
        while not temp_fila.empty():
            self.fila.put(temp_fila.get())
        
        #Salvar no documento
        try:
            with open(self.arquivo_fila, 'wb') as f:
                pickle.dump(emails_pendentes, f)
            self.logger.info(f"Salvos {len(emails_pendentes)} emails pendentes")
        except Exception as e:
            self.logger.error(f"Erro ao salvar emails pendentes: {e}")
    
    def adicionar_email(self, email_task):
        self.fila.put(email_task)
        self.logger.info(f"Email para {email_task.destinatario} adicionado à fila de pendentes")
        self.salvar_fila()
    
    def iniciar_processamento(self, email_sender):
        if self.running:
            self.logger.warning("O processo da fila já está em execução")
            return  # Não tente iniciar novamente
            
        self.running = True
        self.thread = threading.Thread(target=self._processar_fila, args=(email_sender,))
        self.thread.daemon = True
        self.thread.start()
        self.logger.info("Processo da fila de emails pendentes foi iniciado")
    
    def parar_processamento(self):
        """Para o processo da fila de emails pendentes."""
        if not self.running:
            return
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.logger.info("Processo da fila de emails pendentes parado")
        self.salvar_fila()
    
    def _processar_fila(self, email_sender):
        while self.running:
            if self.fila.empty():
                time.sleep(5)
                continue
                
            email_task = self.fila.get()
            
            #Verificar se já passou o intervalo entre as tentativas
            agora = time.time()
            if (email_task.ultima_tentativa and 
                (agora - email_task.ultima_tentativa) < self.intervalo_tentativas):
                #Se ainda não passou o intervalo, voltar para a fila
                self.fila.put(email_task)
                time.sleep(5)
                continue
            
            #Verificar se não ultrapassou o número máximo de tentativas
            if email_task.tentativas >= self.max_tentativas:
                self.logger.warning(f"Email para {email_task.destinatario} ultrapassou o número máximo de tentativas ({self.max_tentativas})")
                continue
                
            #Tentar enviar o email novamente
            try:
                email_task.tentativas += 1
                email_task.ultima_tentativa = agora
                
                sucesso = email_sender.enviar_email(
                    destinatario=email_task.destinatario,
                    nome=email_task.nome,
                    assunto=email_task.assunto,
                    corpo_mensagem=email_task.corpo_mensagem,
                    anexos=email_task.anexos,
                    cc=email_task.cc,
                    bcc=email_task.bcc,
                    html=email_task.html
                )
                
                if not sucesso:
                    #Em caso de falha, adicionar novamente à fila
                    self.fila.put(email_task)
                    self.logger.warning(f"Falha ao reenviar email para {email_task.destinatario} (tentativa {email_task.tentativas}/{self.max_tentativas})")
                else:
                    self.logger.info(f"Email reenviado com sucesso para {email_task.destinatario} após {email_task.tentativas} tentativas")
            except Exception as e:
                #Se ocorrer um erro, registar e adicionar novamente à fila
                email_task.erro = str(e)
                self.fila.put(email_task)
                self.logger.error(f"Erro ao reenviar email para {email_task.destinatario}: {e}")
            
            #Salvar o estado da fila
            self.salvar_fila()
            
            #Pequena pausa para evitar sobrecarregar o sistema
            time.sleep(2)
    
    def listar_emails_pendentes(self):
        """Retorna uma lista dos emails pendentes na fila."""
        emails = []
        temp_fila = Queue()
        while not self.fila.empty():
            email = self.fila.get()
            emails.append(email)
            temp_fila.put(email)
        while not temp_fila.empty():
            self.fila.put(temp_fila.get())
        return emails