# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models


class IrHttp(models.AbstractModel):
    """Extends the 'ir.http' class to include the 'kanban_sticky_state'
     parameter in session info. """
    _inherit = 'ir.http'

    def session_info(self):
        """Overrides the session_info method to include the
        'kanban_sticky_state' parameter."""
        res = super(IrHttp, self).session_info()
        res['is_kanban_sticky_state'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'kanban_sticky_state.is_kanban_sticky_state')
        return res
