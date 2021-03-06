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


# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = 'your_gmail@gmail.com'

def gmail_authenticate():
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

# get the Gmail API service
service = gmail_authenticate()

# utility functions
def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)


def parse_email(payload, folder_name):
    """
    Utility function that parses the content of an email partition
    """
    if payload:
        filename = payload.get("filename")
        mimeType = payload.get("mimeType")
        body = payload.get("body")
        data = body.get("data")
        if mimeType == "text/html":
            # if the email body is an HTML content
            # save the HTML file and optionally open it in the browser
            if not filename:
                filename = "index.html"
            filepath = os.path.join(folder_name, filename)
            print("Saving HTML to", filepath)
            return urlsafe_b64decode(data)
        else:
            raise Exception("This code is not yet equiped to deal with anything else than HTML. Are you sure you sent the right email?")
            

def search_messages(service, query):
    result = service.users().messages().list(userId='me',q=query).execute()
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


def read_message(service, message):
    """
    This function takes Gmail API `service` and the given `message_id` and does the following:
        - Downloads the content of the email
        - Prints email basic information (To, From, Subject & Date) and plain/text body
        - Creates a folder for each email based on the subject
        - Downloads text/html content (if available) and saves it under the folder created as index.html
        - Downloads any file that is attached to the email and saves it in the folder created
    """
    msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
    # parts can be the message body, or attachments
    payload = msg['payload']
    headers = payload.get("headers")
    folder_name = "email"
    has_subject = False
    if headers:
        # this section prints email basic info & creates a folder for the email
        for header in headers:
            name = header.get("name")
            value = header.get("value")
            if name.lower() == 'from':
                # we print the From address
                print("From:", value)
            if name.lower() == "to":
                # we print the To address
                print("To:", value)
            if name.lower() == "subject":
                # make our boolean True, the email has "subject"
                has_subject = True
                # make a directory with the name of the subject
                folder_name = clean(value)
                os.makedirs(folder_name, exist_ok=True)
                print("Subject:", value)
            if name.lower() == "date":
                # we print the date when the message was sent
                print("Date:", value)
    if not has_subject:
        # if the email does not have a subject, then make a folder with "email" name
        # since folders are created based on subjects
        if not os.path.isdir(folder_name):
            os.makedirs(folder_name, exist_ok=True)
    raw_email_html = parse_email(payload, folder_name)
    new_email_content, portal_link = parse_email_html(raw_email_html)
    print(portal_link)
    with open(os.path.join(folder_name, 'defaced_index.html'), "w") as f:
        f.write(str(new_email_content))

    print("="*50)


# get emails that match the query you specify
results = search_messages(service, "billing-no-reply@proximus.com")
# for each email matched, read it (output plain/text to console & save HTML and attachments)
for msg in results:
    read_message(service, msg)