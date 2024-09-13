# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
"""Franchise feedback form"""
from odoo import api, fields, models, _


class DealerSale(models.Model):
    """Franchise Dealer Monthly Sales Feedback."""
    _name = "dealer.sale"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin',
                'utm.mixin']
    _description = "Dealer Sales"
    _rec_name = "dealer_id"

    serial_no = fields.Char(string="Sl No", help='Serial no', readonly=True,
                            copy=False, default='New')
    dealer_id = fields.Many2one('franchise.dealer',
                                string="Franchise Dealer",
                                help='Franchise dealer name')
    franchise_reference = fields.Char(string="Franchise Reference",
                                      readonly=True,
                                      help='Franchise Reference Number')
    dealer_mail = fields.Char(string='mail', help='Franchise Dealer email')
    dealer_agreement_id = fields.Many2one('franchise.agreement',
                                          string="Franchise agreement type",
                                          help='Franchise Agreement Type')
    dealership_signed_on = fields.Date(string='Dealership Signed on',
                                       readonly=True,
                                       help='Dealership Contract Signed on')
    sale_quantity = fields.Integer(string="Sale Quantity",
                                   help='Total Sale Quantity')
    scrap_quantity = fields.Integer(string="Scrap Quantity",
                                    help='Total Scrap Quantity')
    total_sale_amount = fields.Float(string="Sale Amount",
                                     help='Total Sale Amount')
    discount_percentage = fields.Float(string="Discount Given in(%)",
                                       help='Discount Given in(%)')
    monthly_target_amount = fields.Float(string="Monthly Target",
                                         help='Monthly Target Amount')
    monthly_target_gained = fields.Float(string="Monthly Target Gained in (%)",
                                         help='Monthly Target Gained in (%)')
    state = fields.Selection(selection=[('a_to_verify', 'To Verify'),
                                        ('b_verified', 'Verified')],
                             string='Status', required=True,
                             help='Status of the Franchise Registration',
                             readonly=True, copy=False,
                             tracking=True, default='a_to_verify')

    def action_verify_sale(self):
        """Method to verify the sales feedback"""
        self.write({'state': "b_verified"})

    @api.model_create_multi
    def create(self, vals_list):
        """Method to create Franchise dealer sales record sequences."""
        for vals in vals_list:
            if vals.get('serial_no', _("New")) == _("New"):
                vals['serial_no'] = self.env['ir.sequence'].next_by_code(
                    'dealer.sale') or 'New'
            result = super(DealerSale, self).create(vals)
            return result
