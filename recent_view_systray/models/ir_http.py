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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class IrHttp(models.AbstractModel):
    """
    Inherits from 'ir.http' to inject user-specific configuration into the
    session information sent to the web client.
    """
    _inherit = 'ir.http'

    def session_info(self):
        """
        Overrides session_info to include the 'history_limit' for the current
        user, enabling dynamic configuration in the systray history.
        """
        result = super(IrHttp, self).session_info()
        try:
            with self.env.cr.savepoint():
                limit = self.env.user.history_limit or 15
                result['history_limit'] = limit
                if 'user_context' in result:
                    result['user_context']['history_limit'] = limit
        except Exception:
            result['history_limit'] = 15
        return result
