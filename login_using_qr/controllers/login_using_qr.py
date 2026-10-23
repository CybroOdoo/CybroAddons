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
import logging

from odoo import http
from odoo.exceptions import AccessDenied
from odoo.http import Controller, request

from .authenticate import authenticate_without_passwd

_logger = logging.getLogger(__name__)


class LoginController(Controller):
    """Controller handling QR code scanning and authentication."""

    @http.route('/login_using_qr/authenticate', type='jsonrpc', auth='public')
    def scanner(self, scanned_qr):
        """Scan the provided QR token and log in the corresponding internal user.

        Note: Only internal users can log in using this method, and 2FA accounts
        are protected against passwordless bypass.
        """
        if not scanned_qr or not isinstance(scanned_qr, str) or len(scanned_qr.strip()) < 10:
            return False

        db = request.session.db or request.db or (request.env.cr and request.env.cr.dbname)
        if not db:
            _logger.warning("QR login attempt failed: no database found")
            return False

        user = request.env['res.users'].sudo().search([
            ('qr_token', '=', scanned_qr.strip()),
            ('share', '=', False),
            ('active', '=', True),
        ], limit=1)

        if not user:
            _logger.warning("QR login attempt failed: invalid or unknown QR token")
            return False

        if getattr(user, 'totp_enabled', False):
            _logger.warning(
                "QR login attempt rejected: two-factor authentication (2FA) is enabled for user %s",
                user.login,
            )
            return False

        try:
            authenticate_without_passwd(request.session, db, user.login)
            return True
        except AccessDenied as e:
            _logger.error("QR login authentication failed for %s: %s", user.login, e)
            return False
