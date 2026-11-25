# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class MenuPassword(models.Model):
    """Inverse model for one to many field of the model res users"""
    _name = 'menu.password'
    _description = 'Menus and Corresponding Locks for multiple password lock '

    menus_id = fields.Many2one('ir.ui.menu', string="Menus",
                               help='Select the menus to lock',
                               domain="[('parent_id','=',False)]")
    password = fields.Char(
        string='Menu Password', groups='base.group_system', copy=False,
        compute='_compute_password', inverse='_set_password')
    menu_lock_hash = fields.Char(groups='base.group_system', copy=False)
    password_length = fields.Integer(groups='base.group_system', copy=False)
    has_password = fields.Boolean(
        compute='_compute_has_password', groups='base.group_system')
    password_id = fields.Many2one('res.users', string='Password',
                                  help='Inverse field to res user model')

    @api.depends('menu_lock_hash')
    def _compute_has_password(self):
        for line in self:
            line.has_password = bool(line.menu_lock_hash)

    def _compute_password(self):
        self.password = False

    def _set_password(self):
        context = self.env['res.users']._crypt_context()
        for line in self:
            value = line.password
            line.write({
                'menu_lock_hash': context.hash(value) if value else False,
                'password_length': len(value) if value else 0,
            })
        self.invalidate_recordset(['password'])
