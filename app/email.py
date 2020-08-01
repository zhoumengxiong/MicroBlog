from flask_mail import Message
from app import mail, app
from flask import render_template, flash
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    From, To, PlainTextContent, HtmlContent, Mail)
import os
from threading import Thread


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email('[Microblog] Reset Your Password',
               sender=app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token)
               )


# send mail with SendGrip
def send_api_mail(user):
    token = user.get_reset_password_token()
    from_email = From('zhou_cba@163.com')
    to_email = To(user.email)
    subject = '[Microblog] Reset Your Password'
    plain_text_content = PlainTextContent(render_template('email/reset_password.txt',
                                                          user=user, token=token)
                                          )
    html_content = HtmlContent(render_template('email/reset_password.html',
                                               user=user, token=token))
    message = Mail(from_email, to_email, subject,
                   plain_text_content, html_content)
    Thread(target=send_api_mail_async, args=(message,)).start()
    flash('Email Sent!')


def send_api_mail_async(message):
    sendgrid_client = SendGridAPIClient(
        api_key=os.environ.get('SENDGRID_API_KEY'))
    # with app.app_context():
    sendgrid_client.send(message=message)
