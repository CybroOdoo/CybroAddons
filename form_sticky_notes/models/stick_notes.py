"""Sticky notes"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class StickyNotes(models.Model):
    """The sticky note class"""
    _name = 'stick.notes'
    _description = 'Stick notes'

    notes = fields.Text(string='Notes', help="Notes of sticky")
    created_id = fields.Many2one('res.users',
                                 default=lambda self: self.env.user,
                                 string="Created By", help='Notes created user')
    date = fields.Date(default=fields.Date.today(), string="Date",
                       help="Creation date of the form")
    related_model_name = fields.Char(string='Related Model',
                                     help="Name of the related model")
    related_model = fields.Integer(string='Related Model Id',
                                   help=" Id of the related model")
