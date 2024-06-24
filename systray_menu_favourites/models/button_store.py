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
from odoo import api, fields, models


class ButtonStore(models.Model):
    """To store the details of each button which are created in the UI,
    and it will remove from the model when the button removed from UI"""
    _name = 'button.store'
    _description = 'Button Store'

    name = fields.Char(string='Name',
                       help='Name of the button which stored')
    button = fields.Integer(string='Button ID',
                            help='To store the button ID to '
                                 'identify the menu data'
                            )

    @api.model
    def action_create(self, vals, button):
        """Add the details of button when button created,
         and it can be used after restart the page to restore the button"""
        val = {'name': vals, 'button': button}
        self.env['button.store'].sudo().create(val)

    @api.model
    def action_search(self):
        """Return the details of button, when restart the page,
        data will be restored from the database"""
        datas = [{'name': val.name, 'button': val.button} for val in
                 self.env['button.store'].sudo().search([])]
        return datas

    @api.model
    def action_remove_view(self, value):
        """Remove the record when the button is deleted,
        data will be removed, to avoid the conflicts"""
        vals = self.env['button.store'].sudo().search([('button', '=',
                                                        value)])
        vals.unlink()
