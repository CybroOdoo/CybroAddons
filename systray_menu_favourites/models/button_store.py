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


class ButtonStore(models.Model):
    _name = 'button.store'
    _description = 'Button ID'

    name = fields.Char()
    button_id = fields.Integer()

    """Add the details of button when button created"""

    @api.model
    def create_button(self, vals, button_id):
        val = {
            'name': vals,
            'button_id': button_id
        }
        self.env['button.store'].sudo().create(val)

    """return the details of button"""

    @api.model
    def search_button(self):
        vals = self.env['button.store'].sudo().search([])
        datas = []
        for val in vals:
            data = {
                'name': val.name,
                'button_id': val.button_id,
            }
            datas.append(data)
        return datas

    """remove the record when the button is deleted"""

    @api.model
    def remove_view(self, value):
        vals = self.env['button.store'].sudo().search([('button_id', '=', value)])
        vals.unlink()
