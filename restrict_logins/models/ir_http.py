# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from datetime import timedelta

from odoo import fields, models, SUPERUSER_ID
from odoo.http import request

from ..utils import writable_cursor

_logger = logging.getLogger(__name__)

# Minimum delay (in seconds) between two refreshes of the stored session.
REFRESH_DELAY = 30


class IrHttp(models.AbstractModel):
    """Keeps the session details of the user up to date on each request."""
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        """Refresh the stored session details of the logged-in user, then
        run the standard authentication."""
        try:
            cls._refresh_user_session()
        except Exception:  # pylint: disable=broad-except
            _logger.info("Exception during updating user session.",
                         exc_info=True)
        return super()._authenticate(endpoint)

    @classmethod
    def _refresh_user_session(cls):
        """Store the current session id and push the expiry date forward when
        the stored session is missing, differs or is older than the delay."""
        uid = request.session.uid
        if not uid:
            return
        user = request.env['res.users'].with_user(SUPERUSER_ID).browse(uid)
        sid = request.session.sid
        now = fields.Datetime.now()
        stale = (not user.last_update
                 or (now - user.last_update).total_seconds() > REFRESH_DELAY)
        if sid == user.sid and not stale:
            return
        minutes = user._get_session_expire_minutes()
        user.flush_recordset(
            ['sid', 'last_update', 'exp_date', 'logged_in'])
        with writable_cursor(request.env) as cursor:
            cursor.execute(
                """UPDATE res_users
                      SET sid = %s, last_update = %s, exp_date = %s,
                          logged_in = TRUE
                    WHERE id = %s""",
                (sid, now, now + timedelta(minutes=minutes), uid))
        user.invalidate_recordset(
            ['sid', 'last_update', 'exp_date', 'logged_in'])
