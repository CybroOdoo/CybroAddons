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

from odoo import SUPERUSER_ID, api
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.http.session import finalize
from odoo.modules.registry import Registry
from odoo.tools.misc import get_lang

_logger = logging.getLogger(__name__)


def authenticate_without_passwd(session, dbname, login):
    """Authenticate an HTTP session for the given login without requiring a password."""
    registry = Registry(dbname)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        user = env['res.users'].search([('login', '=', login)], limit=1)
        if not user:
            raise AccessDenied()
        pre_uid = user.id
        session['pre_login'] = login
        session['pre_uid'] = pre_uid
        finalize(session, env)

    try:
        if request and request.session is session and (request.db == dbname or not request.db):
            if hasattr(request, 'update_env') and getattr(request, 'env', None):
                request.update_env(user=session.uid, context=session.context)
                request.update_context(lang=get_lang(request.env(user=session.uid)).code)
    except RuntimeError:
        _logger.debug("Request is not bound in a non-HTTP context")
    return session.uid
