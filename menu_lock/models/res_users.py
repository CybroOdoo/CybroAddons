# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class ResUsers(models.Model):
    """Inherited the res_users model for adding the fields for menu lock
    setup."""
    _inherit = 'res.users'

    password_lock = fields.Selection(
        [('single_password', 'Single Password Lock'),
         ('multi_password', 'Multi Password Lock')],
        string='Menu Lock Password Type',
        help='Type of Menu Lock Password')
    login_password = fields.Char(string='Login Password', help='Login Password')
    menus_to_lock_ids = fields.Many2many('ir.ui.menu', string="Menus to lock",
                                         domain="[('parent_id','=',False)]",
                                         help='Select the menus to lock')
    multi_lock_ids = fields.One2many('menu.password', 'password_id',
                                     string='Multi menus to lock',
                                     help='Multi lock menus and password')
    models_to_lock_ids = fields.Many2many('ir.model', string='Models to lock')

    @api.model
    def menu_lock_search(self, args):
        """Method to returning values though args"""
        user = self.env['res.users'].browse(args)
        lock_models = user.models_to_lock_ids.mapped('model')
        return {
            'multi_lock_ids': [{
                'id': menu.menus_id.id,
                'password': menu.password
            } for menu in user.multi_lock_ids],
            'locked_menu_ids': user.menus_to_lock_ids.ids,
            'lock_type': user.password_lock,
            'locked_models': True if lock_models else False,
            'login_password': user.login_password
            if user.password_lock == 'single_password' else False,
        }

    @api.onchange('menus_to_lock_ids')
    def _onchange_menus_to_lock_ids(self):
        """Method to add fields from single password option to one-to-many of
         multi password with same password in onchange of the field"""
        if self.password_lock == 'single_password':
            new_lines = [(5, 0, 0)]
            for rec in self.menus_to_lock_ids:
                new_lines.append(
                    (0, 0, {'menus_id': rec._origin.id,
                            'password': self.login_password,
                            }))
            self.write({'multi_lock_ids': new_lines})
