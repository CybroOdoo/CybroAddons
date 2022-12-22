# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
'''Module for Creating Animal Records'''
from odoo import models, fields


class AnimalDetails(models.Model):
    '''Details of Animals'''
    _name = 'animal.details'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Animal Details"
    _rec_name = 'breed'

    image = fields.Binary(string='Image', tracking=True)
    breed = fields.Char(string='Breed', required=True, tracking=True)
    age = fields.Char(string='Age', required=True, tracking=True)
    state = fields.Selection(
        [('available', 'Available'), ('not_available', 'Not Available')],
        default="available",
        string='Status', required=True, tracking=True)
    note = fields.Text(string='Note', tracking=True)

    def action_not_available(self):
        self.state = 'not_available'

    def action_sold(self):
        self.state = 'sold'

    def action_available(self):
        self.state = 'available'
