"""This service will simply check my mailbox for any new emails that need to be processed."""
# Use RQ as our task queue
from redis import Redis
from rq import Queue

import email_utils
import worker
import config


def poll_mailbox():
    """Poll gmail mailbox and search for messages we need to process.

    Returns:
        list: List of gmail messages to process.
    """
    # get the Gmail API service
    service = email_utils.gmail_authenticate()
    # get emails that match the query you specify
    results = email_utils.search_messages(service, config.MAIL_SEARCH_QUERY)
    print(results)

    # # for each email matched, read it (output plain/text to console & save HTML and attachments)
    # for msg in results:
    #     gmail_utils.read_message(service, msg)
    return results


if __name__ == '__main__':
    q = Queue(connection=Redis())
    mails_to_process = poll_mailbox()
    for mail in mails_to_process:
        q.enqueue(worker.process_email, mail)
