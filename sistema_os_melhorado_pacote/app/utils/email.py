"""
Utilitários para envio de emails.
Este módulo contém funções para envio de emails em diferentes contextos da aplicação.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app


def send_email(subject, body, to_email=None, html=False):
    """
    Envia um email com o assunto e corpo especificados.
    
    Args:
        subject (str): Assunto do email
        body (str): Corpo do email
        to_email (str, optional): Destinatário do email. Se não for especificado,
                                 usa o email padrão configurado na aplicação.
        html (bool, optional): Se True, envia o email como HTML. Default é False.
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário.
    """
    if to_email is None:
        to_email = current_app.config['EMAIL_DESTINATARIO']
    
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = current_app.config['EMAIL_USER']
    msg['To'] = to_email
    
    if html:
        msg.attach(MIMEText(body, 'html'))
    else:
        msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP(current_app.config['EMAIL_HOST'], current_app.config['EMAIL_PORT']) as server:
            server.starttls()
            server.login(current_app.config['EMAIL_USER'], current_app.config['EMAIL_PASSWORD'])
            server.sendmail(current_app.config['EMAIL_USER'], to_email, msg.as_string())
        return True
    except Exception as e:
        current_app.logger.error(f'Erro ao enviar e-mail: {str(e)}')
        return False


def send_notification_email(subject, body, to_email=None):
    """
    Envia um email de notificação com formatação padrão.
    
    Args:
        subject (str): Assunto do email
        body (str): Corpo do email
        to_email (str, optional): Destinatário do email
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário.
    """
    html_body = f"""
    <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1a3c34; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; border: 1px solid #ddd; }}
                .footer {{ text-align: center; margin-top: 20px; font-size: 12px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{subject}</h2>
                </div>
                <div class="content">
                    {body}
                </div>
                <div class="footer">
                    <p>Este é um email automático, por favor não responda.</p>
                    <p>&copy; {current_app.config.get('APP_NAME', 'Sistema OS')} {current_app.config.get('APP_YEAR', '2025')}</p>
                </div>
            </div>
        </body>
    </html>
    """
    return send_email(subject, html_body, to_email, html=True)


def send_welcome_email(user_name, user_email):
    """
    Envia um email de boas-vindas para um novo usuário.
    
    Args:
        user_name (str): Nome do usuário
        user_email (str): Email do usuário
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário.
    """
    subject = "Bem-vindo ao Sistema de OS"
    body = f"""
    <p>Olá {user_name},</p>
    <p>Bem-vindo ao Sistema de Ordens de Serviço! Sua conta foi criada com sucesso.</p>
    <p>Você pode acessar o sistema com seu email: <strong>{user_email}</strong></p>
    <p>Se você tiver alguma dúvida, entre em contato com o administrador do sistema.</p>
    <p>Atenciosamente,<br>Equipe do Sistema OS</p>
    """
    return send_notification_email(subject, body, user_email)


def send_password_reset_email(user_name, user_email, reset_link):
    """
    Envia um email com link para redefinição de senha.
    
    Args:
        user_name (str): Nome do usuário
        user_email (str): Email do usuário
        reset_link (str): Link para redefinição de senha
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário.
    """
    subject = "Redefinição de Senha"
    body = f"""
    <p>Olá {user_name},</p>
    <p>Recebemos uma solicitação para redefinir sua senha.</p>
    <p>Clique no link abaixo para redefinir sua senha:</p>
    <p><a href="{reset_link}">{reset_link}</a></p>
    <p>Se você não solicitou a redefinição de senha, ignore este email.</p>
    <p>Atenciosamente,<br>Equipe do Sistema OS</p>
    """
    return send_notification_email(subject, body, user_email)


def send_ordem_status_update_email(ordem, user_name, user_email):
    """
    Envia um email de atualização de status de uma ordem de serviço.
    
    Args:
        ordem (OrdemServico): Ordem de serviço atualizada
        user_name (str): Nome do usuário
        user_email (str): Email do usuário
    
    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário.
    """
    subject = f"Atualização de Ordem de Serviço #{ordem.id}"
    body = f"""
    <p>Olá {user_name},</p>
    <p>A Ordem de Serviço #{ordem.id} foi atualizada para o status: <strong>{ordem.status}</strong></p>
    <p><strong>Descrição:</strong> {ordem.descricao}</p>
    <p><strong>Condomínio:</strong> {ordem.condominio.nome}</p>
    <p><strong>Prioridade:</strong> {ordem.prioridade}</p>
    <p>Para mais detalhes, acesse o sistema.</p>
    <p>Atenciosamente,<br>Equipe do Sistema OS</p>
    """
    return send_notification_email(subject, body, user_email)
