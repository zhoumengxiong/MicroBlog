from flask import render_template, flash, current_app  # from_email = current_app.config['ADMINS'][0]
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import From, To, PlainTextContent, HtmlContent, Mail
import os
from threading import Thread


# send mail with SendGrip
def send_api_mail_async(user):
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
    Thread(target=send_api_mail, args=(message,)).start()
    flash('Email Sent!')


def send_api_mail(message):
    sendgrid_client = SendGridAPIClient(
        api_key=os.environ.get('SENDGRID_API_KEY'))
    # with app.app_context():
    sendgrid_client.send(message=message)
