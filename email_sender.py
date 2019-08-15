import smtplib

# Import the email modules we'll need
from email.message import EmailMessage


def send_gmail(message, recipient, user_gmail, user_password, subject="Automatic Notification"):
    fromaddr = user_gmail
    toaddr = recipient
    msg = EmailMessage()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = subject

    msg.set_content(message)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, user_password)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()

    # send_email("test test test")
