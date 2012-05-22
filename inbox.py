# -*- coding: utf-8 -*-

import argparse
from email.parser import Parser

import gevent
import gevent.monkey

from logbook import Logger

gevent.monkey.patch_select()

import smtpd
import asyncore


log = Logger(__name__)


class InboxServer(smtpd.SMTPServer, object):
    """Logging-enabled SMTPServer instance with handler support."""

    def __init__(self, handler, *args, **kwargs):
        super(InboxServer, self).__init__(*args, **kwargs)
        self._handler = handler

    def process_message(self, peer, mailfrom, rcpttos, data):
        log.info('Collating message from {0}'.format(mailfrom))
        subject = Parser().parsestr(data)['subject']
        log.debug(dict(to=rcpttos, sender=mailfrom, subject=subject, body=data))
        return self._handler(to=rcpttos, sender=mailfrom, subject=subject, body=data)


class Inbox(object):
    """A simple SMTP Inbox."""

    def __init__(self, port=None, address=None):
        self.port = port
        self.address = address
        self.collator = None

    def collate(self, collator):
        """Function decorator. Used to specify inbox handler."""
        self.collator = collator
        return collator

    def serve(self, port=None, address=None, log_level='INFO'):
        """Serves the SMTP server on the given port and address."""
        port = port or self.port
        address = address or self.address
        log.level_name = log_level

        log.info('Starting SMTP server at {0}:{1} with {2} level logging'.format(address, port, log_level))

        server = InboxServer(self.collator, (address, port), None)

        try:
            asyncore.loop()
        except KeyboardInterrupt:
            log.info('Cleaning up')

    def dispatch(self):
        """Command-line dispatch."""
        parser = argparse.ArgumentParser(description='Run an Inbox server.')
        log_choices = ['critical', 'error', 'warning', 'notice', 'info', 'debug']

        parser.add_argument('-a', '--addr', metavar='addr', type=str, help='addr to bind to', required=True)
        parser.add_argument('-p', '--port', metavar='port', type=int, help='port to bind to', required=True)
	    parser.add_argument('-l', '--log', metavar='log', type=str, help='logging level (%s)' % (','.join(log_choices)), default='info', choices=log_choices)

        args = parser.parse_args()

        self.serve(port=args.port, address=args.addr, log_level=args.log.upper())
