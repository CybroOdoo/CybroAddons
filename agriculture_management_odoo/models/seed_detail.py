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


class SeedDetail(models.Model):
    """This model represents comprehensive details about seeds within the
    context of agriculture management. It provides a structured way to store
    information related to various types of seeds used for planting and
    cultivation."""
    _name = 'seed.detail'
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Seed Details In Agriculture Management"

    name = fields.Char(string='Name', help='Mention the name of the breed of '
                                           'crop used for farming',
                       required=True, tracking=True)
    quantity = fields.Integer(string='Quantity', required=True, tracking=True,
                              help='Mention Quantity or seed purchased for '
                                   'farming')
    unit = fields.Selection([('kg', 'Kilograms'), ('gms', 'Grams')],
                            string='Unit', required=True, tracking=True,
                            help='Mention the quantity of seed purchased for '
                                 'farming')
    seed_type = fields.Selection(
        [('registered', 'Registered'), ('breeder', 'Breeder'),
         ('foundation', 'Foundation'),
         ('certified', 'Certified')], string='Type', tracking=True,
        help='Mention the status of seed purchased for farming', required=True)
    note = fields.Text(string='Note', tracking=True,
                       help="Please describe any additional details here if "
                            "there is a need to mention additional data.")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, help='The company associated with the current user or '
        'environment.', default=lambda self: self.env.company)
