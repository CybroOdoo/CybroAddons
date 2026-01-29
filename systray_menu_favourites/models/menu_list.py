# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import api, fields, models


class MenuList(models.Model):
    _inherit = 'ir.ui.menu'

    """return the details of view"""

    @api.model
    def search_views(self, value):
        vals = self.env['ir.ui.menu'].sudo().browse(value)
        query = """SELECT action FROM ir_ui_menu
                    WHERE id = '%d'""" % (int(vals.id))
        self._cr.execute(query)
        data = self._cr.dictfetchall()
        word = data[0]['action']
        if word:
            val = word.find(',')
            action_id = word[val + 1:]

            act = self.env['ir.actions.act_window'].sudo().browse(int(action_id))
            view = act.view_mode
            if view:
                view = act.view_mode.split(',')
                if view[0] == 'tree':
                    val = {
                        'name': act.name,
                        'model': act.res_model,
                        'view': 'list',
                        'target': act.target
                    }
                else:
                    val = {
                        'name': act.name,
                        'model': act.res_model,
                        'view': view[0],
                        'target': act.target
                    }
            return val
