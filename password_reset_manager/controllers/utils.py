# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import threading
import time
from collections import defaultdict, deque

from werkzeug.exceptions import NotFound

from odoo.http import request

MAX_FAILED_ATTEMPTS = 5
BLOCK_WINDOW = 600  # seconds

_failed_attempts = defaultdict(deque)
_lock = threading.Lock()


def check_reset_password_enabled(controller):
    """Return the signup qcontext, or raise a 404 when the password reset
    option is disabled in the general settings (same flag that hides the
    login page links)."""
    qcontext = controller.get_auth_signup_qcontext()
    if not qcontext.get('reset_password_enabled'):
        raise NotFound()
    return qcontext


def _client_key(scope):
    return '%s:%s' % (scope, request.httprequest.remote_addr)


def is_throttled(scope):
    """Return True if the client made too many failed attempts recently."""
    key = _client_key(scope)
    now = time.monotonic()
    with _lock:
        attempts = _failed_attempts[key]
        while attempts and now - attempts[0] > BLOCK_WINDOW:
            attempts.popleft()
        return len(attempts) >= MAX_FAILED_ATTEMPTS


def register_failure(scope):
    """Record a failed attempt for the current client."""
    with _lock:
        _failed_attempts[_client_key(scope)].append(time.monotonic())


def reset_failures(scope):
    """Forget the failed attempts of the current client."""
    with _lock:
        _failed_attempts.pop(_client_key(scope), None)
