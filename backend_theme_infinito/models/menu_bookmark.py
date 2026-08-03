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
from odoo import api, fields, models


class InfinitoMenuBookmark(models.Model):
    """
    Model representing bookmarks for menu items in the Infinito system.
    """
    _name = 'infinito.menu.bookmark'
    _description = 'Menu Bookmark'

    name = fields.Char('Name', default='Bookmark')
    action_id = fields.Many2one('ir.actions.actions', ondelete='cascade', db_constraint=False)
    menu_id = fields.Many2one('ir.ui.menu', ondelete='cascade', db_constraint=False)
    url = fields.Text('Url')
    user_id = fields.Many2one('res.users')

    @api.model
    def _valid_field_parameter(self, field, name):
        return name == 'db_constraint' or super()._valid_field_parameter(field, name)
