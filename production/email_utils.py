import base64
import email.encoders
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode
# for parsing the email html content
from bs4 import BeautifulSoup

import config


# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']

def gmail_authenticate():
    """Authenticate to the gmail api using a json containing the gcp credentials.
    Save the returned token to a pickle file to be reused.

    Returns:
        gmail_client: The gmail API client with an active session.
    """
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


def parse_email(payload):
    """Parse raw email and return the actualy content (payload)

    Args:
        payload (Message.MessagePart): https://developers.google.com/gmail/api/reference/rest/v1/users.messages#Message.MessagePart

    Raises:
        Exception: Will raise exception when email content is not html

    Returns:
        data: email data content as a b64 encoded string
    """
    if payload:
        filename = payload.get("filename")
        mimeType = payload.get("mimeType")
        body = payload.get("body")
        data = body.get("data")
        if mimeType == "text/html":
            return urlsafe_b64decode(data)
        else:
            raise Exception("This code is not yet equiped to deal with anything else than HTML. Are you sure you sent the right email?")
            

def search_messages(service, query):
    """Search inbox for messages given a search query

    Args:
        service (_type_): Gmail API client
        query (str): Gmail search query, follows same pattern as in web UI

    Returns:
        list: list of Messages that the query returned
    """
    result = service.users().messages().list(userId='me', q=query).execute()
    messages = [ ]
    if 'messages' in result:
        messages.extend(result['messages'])
    while 'nextPageToken' in result:
        page_token = result['nextPageToken']
        result = service.users().messages().list(userId='me', q=query, pageToken=page_token).execute()
        if 'messages' in result:
            messages.extend(result['messages'])
    return messages


def deface(soup):
    """Deface the original proximus mail content

    Args:
        soup (Beautifulsoup): soup of the original proximus html mail content

    Returns:
        Beautifulsoup: Defaced html for the reply email
    """
    header_image = soup.find_all('img')[0]
    header_image['src'] = "https://i.imgur.com/Y6H2R3o.jpeg"
    text_blocks = soup.find_all('span')
    for text_block in text_blocks:
        if not text_block.string:
            continue
        if text_block.string.startswith("Uw nieuwe factuur"):
            text_block.string = "Uw nieuwe factuur zit gewoon in bijlage."
        if text_block.string.startswith("U kan deze heel eenvoudig in"):
            text_block.string = "Het is niet meer nodig om die in\n\r"
        if "bekijken" in text_block.string:
            text_block.string = " te bekijken."
        if text_block.string.startswith("Uw Proximus-team"):
            text_block.string = "Uw Corporate Overlords"
    print(soup.prettify())
    return soup


def parse_email_html(raw_email_html):
    """Get the proximus portal link and deface the contents

    Args:
        raw_email_html (str): String html content of the original email

    Raises:
        Exception: Raises an exception if the correct portal link is not found.

    Returns:
        tuple: The defaced html as a Beautifulsoup and the portal link as string 
    """
    # Get the required link from the email body
    soup = BeautifulSoup(raw_email_html, 'html.parser')
    # TODO: deface the email itself
    for link in soup.find_all('a'):
        if link.string == "MyProximus":
            portal_link = link.get("href")
            # Deface the return email, because they deserve it
            defaced_soup = deface(soup)
            return str(defaced_soup), portal_link
    raise Exception("Didn't find the right MyProximus link!")


def mark_processed(service, mail_info):
    """Mark the incoming email with a specific label to make sure it's not pulled in twice

    Args:
        service (_type_): Gmail API Client
        mail_info (dict): Dict with returned info about specific email from API
    """
    request_body = {
        # ProcessedInvoices Label
        "addLabelIds": ["Label_586225920876536968"],
        # Remove from inbox and send to above ID "folder"
        "removeLabelIds": ["INBOX"]
    }
    service.users().messages().modify(userId='me', id=mail_info['id'], body=request_body).execute()


def send_reply(service, payload, attachment_path):
    """Send the reply email given the contents

    Args:
        service (gmail_client): Gmail API client
        payload (str): html to use as email body
        attachment_path (str): path to the pdf to attach

    Returns:
        Message: The gmail API response Message
    """
    # Set the basic metadata of the email
    message = MIMEMultipart('mixed')
    message['To'] = config.TO
    message['From'] = config.FROM
    message['Subject'] = config.SUBJECT

    # The html content of the mail itself
    msg = MIMEText(payload, 'html')
    message.attach(msg)

    # Set the attachment, we know this will always be a pdf
    with open(attachment_path, 'rb') as fp:
        attachment = MIMEApplication(fp.read(), _subtype="pdf")

    filename = os.path.basename(attachment_path)
    attachment.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(attachment)

    encoded_message = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}

    reply = (service.users().messages().send(userId='me', body=encoded_message).execute())
    print('Message Id: %s' % reply['id'])
    return reply
