# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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


class AnimalDetail(models.Model):
    """This model represents comprehensive details about animals involved
     in agricultural management. It provides a structured way to store
     information related to various animal breeds and their attributes."""
    _name = 'animal.detail'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Animal Details in Agriculture Management"
    _rec_name = 'breed'

    image = fields.Binary(string='Image', help='Upload images of animals',
                          tracking=True)
    breed = fields.Char(string='Breed', help='Mention the breed of animal',
                        required=True, tracking=True)
    age = fields.Char(string='Age', help='Mention the age of animal',
                      required=True, tracking=True)
    state = fields.Selection(
        [('available', 'Available'), ('not_available', 'Not Available')],
        default="available", help='The status whether this animal, whether it '
                                  'is available or not',
        string='Status', required=True, tracking=True)
    note = fields.Text(string='Note', tracking=True,
                       help='If any notes or description about the animal')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, help='This field represents the company associated with '
        'the current user or environment.', default=lambda self: self.env.company)

    def action_not_available(self):
        """Function for change state to not available"""
        self.state = 'not_available'

    def action_available(self):
        """Function for change state to available"""
        self.state = 'available'
