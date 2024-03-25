from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ssl
import smtplib
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import ssl

email_password = os.environ.get('email_password')


def send_confirmation_to_client_email(receiver_mail, account_name):
    logo_path = 'discord_app_assets/connectify_icon.png'
    connectify_account = account_name
    from_email = "appmails742@gmail.com"
    password = email_password
    to_email = receiver_mail
    subject = "Welcome to connectify!"
    body = f"""
    Hi {connectify_account},
    Welcome to Connectify. Your new account comes with access to Connectify products, apps, and services.
    """

    em = MIMEMultipart()
    em['From'] = from_email
    em['To'] = to_email
    em['Subject'] = subject

    body_text = MIMEText(body, 'plain')
    em.attach(body_text)

    context = ssl.create_default_context()

    with open(logo_path, 'rb') as logo_file:
        logo_content = logo_file.read()
        logo_attachment = MIMEImage(logo_content, name='logo.png')
        em.attach(logo_attachment)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(from_email, password)
        smtp.sendmail(from_email, to_email, em.as_string())


def send_login_code_to_client_email(code, receiver_mail, account_name):
    logo_path = 'discord_app_assets/connectify_icon.png'
    from_email = "appmails742@gmail.com"
    password = email_password  # Ensure you have email_password defined somewhere
    to_email = receiver_mail
    subject = "Login Verification Code for Connectify"
    body = f"""
    <p>
        Dear {account_name},<br><br>

        We received a login request for your Connectify Account. Your verification code is:<br><br>

        <strong>{code}</strong><br><br>

        If you did not initiate this login attempt, please ignore this email.<br><br>

        Sincerely yours,<br><br>

        The Connectify Team
    </p>
    <img src="cid:logo">  <!-- This references the inline image -->
    """

    em = MIMEMultipart()
    em['From'] = from_email
    em['To'] = to_email
    em['Subject'] = subject

    # Attach HTML body
    body_html = MIMEText(body, 'html')
    em.attach(body_html)

    # Attach inline logo
    with open(logo_path, 'rb') as logo_file:
        logo_attachment = MIMEImage(logo_file.read(), name='logo.png')
        logo_attachment.add_header('Content-ID', '<logo>')
        em.attach(logo_attachment)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(from_email, password)
        smtp.sendmail(from_email, to_email, em.as_string())


def send_sing_up_code_to_client_email(code, receiver_mail, account_name):
    logo_path = 'discord_app_assets/connectify_icon.png'
    connectify_account = account_name
    from_email = "appmails742@gmail.com"
    password = email_password
    to_email = receiver_mail
    subject = "Verification code for Connectify"
    body = f"""
    <p>
        Dear {to_email},<br><br>

        We received a request to create your Connectify Account through our website. Your Connectify verification code is:<br><br>

        <strong>{code}</strong><br><br>

        If you did not request this code, it is possible that someone else is trying to create your Connectify Account - {connectify_account}. Do not forward or give this code to anyone.<br><br>

        You received this message because this email address is listed as the email to create your Connectify Account - {connectify_account}. If that is incorrect, please visit our site to remove your email from a Connectify Account.<br><br>

        Sincerely yours,<br><br>

        The Connectify Accounts team
    </p>
    <img src="cid:logo">  <!-- This references the inline image -->
    """

    em = MIMEMultipart()
    em['From'] = from_email
    em['To'] = to_email
    em['Subject'] = subject

    # Attach HTML body
    body_html = MIMEText(body, 'html')
    em.attach(body_html)

    # Attach inline logo
    with open(logo_path, 'rb') as logo_file:
        logo_attachment = MIMEImage(logo_file.read(), name='logo.png')
        logo_attachment.add_header('Content-ID', '<logo>')
        em.attach(logo_attachment)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(from_email, password)
        smtp.sendmail(from_email, to_email, em.as_string())


def send_forget_password_code_to_email(code, receiver_mail, account_name):
    logo_path = 'discord_app_assets/connectify_icon.png'
    connectify_account = account_name
    from_email = email_password
    password = "faxetenwsyseyikl"
    to_email = receiver_mail
    subject = "Verification code for Connectify"
    body = f"""
    <p>
        Dear {to_email},<br><br>

        We received a request to reset your Connectify Account's Password through our website. Your Connectify verification code is:<br><br>

        <strong>{code}</strong><br><br>

        If you did not request this code, it is possible that someone else is trying to change your Connectify Account Password- {connectify_account}. Do not forward or give this code to anyone.<br><br>

        You received this message because this email address is listed as the email of your Connectify Account - {connectify_account}. If that is incorrect, please visit our site to remove your email from a Connectify Account.<br><br>

        Sincerely yours,<br><br>

        The Connectify Accounts team
    </p>
    <img src="cid:logo">  <!-- This references the inline image -->
    """

    em = MIMEMultipart()
    em['From'] = from_email
    em['To'] = to_email
    em['Subject'] = subject

    # Attach HTML body
    body_html = MIMEText(body, 'html')
    em.attach(body_html)

    # Attach inline logo
    with open(logo_path, 'rb') as logo_file:
        logo_attachment = MIMEImage(logo_file.read(), name='logo.png')
        logo_attachment.add_header('Content-ID', '<logo>')
        em.attach(logo_attachment)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(from_email, password)
        smtp.sendmail(from_email, to_email, em.as_string())


def send_changed_password_to_email(receiver_mail, account_name):
    logo_path = 'discord_app_assets/connectify_icon.png'
    connectify_account = account_name
    from_email = "appmails742@gmail.com"
    password = email_password
    to_email = receiver_mail
    subject = "Welcome to connectify!"
    body = f"""
    Hello {connectify_account},
 	You have successfully changed your Connectify account password. If you did not make this request, please reset the passwords of your email address and Connectfiy account.
 	Thank you,
The Connectify Team
    """

    em = MIMEMultipart()
    em['From'] = from_email
    em['To'] = to_email
    em['Subject'] = subject

    body_text = MIMEText(body, 'plain')
    em.attach(body_text)

    context = ssl.create_default_context()

    with open(logo_path, 'rb') as logo_file:
        logo_content = logo_file.read()
        logo_attachment = MIMEImage(logo_content, name='logo.png')
        em.attach(logo_attachment)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(from_email, password)
        smtp.sendmail(from_email, to_email, em.as_string())
# Example usage:

