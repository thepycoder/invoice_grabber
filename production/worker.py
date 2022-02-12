import email_utils
import proximus


def process_email(mail_info):
    try:
        # get the Gmail API service
        service = email_utils.gmail_authenticate()

        # Get the specific mail we got from the poller
        mail = service.users().messages().get(userId='me', id=mail_info['id'], format='full').execute()
        

        payload = mail['payload']
        raw_email_html = email_utils.parse_email(payload)
        new_email_content, portal_link = email_utils.parse_email_html(raw_email_html)
        pdf_location = proximus.navigate_proximus(portal_link)
        email_utils.send_reply(new_email_content, pdf_location)

        return {'SUCCESS': True}
    except Exception as e:
        return {'SUCCESS': False, 'LOG': e}
