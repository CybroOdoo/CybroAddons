# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Jumana Haseen (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models


class IrUiMenu(models.Model):
    """Inherit model to collect and send back the menu based on the search"""
    _inherit = 'ir.ui.menu'

    @api.model
    def search_views(self, value):
        """Return the details of view, when search the menu in systray,
         send the all related menus"""
        menu_record = self.env['ir.ui.menu'].browse(int(value))
        query = \
            """
                SELECT action FROM ir_ui_menu
                WHERE id = %d
            """ \
            % menu_record.id
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        if not data:
            return None
        action_id = int(data[0]['action'].split(',')[1].strip())
        act = self.env['ir.actions.act_window'].sudo().browse(action_id)
        val = {
            'name': act.name,
            'model': act.res_model,
            'view_mode': act.view_mode,
            'target': act.target,
        }
        return val
