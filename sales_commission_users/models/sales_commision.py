# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (<https://www.cybrosys.com>)
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


class SalesCommission(models.Model):
    """Creating sales commission model."""
    _name = "sales.commission"
    _description = "Sales Commission"

    name = fields.Char(string="Commission Name", help="Name of the commission", required=True)
    sales_person_ids = fields.Many2many('res.users', string='Sales Person',
                                        help="Sales person")
    commission_type = fields.Selection(
        string="Commission Type",
        selection=[('standard', 'Standard'),
                   ('partner_based', 'Partner Based'),
                   ('product_based', 'Product Based'),
                   ('discount_based', 'Discount Based')
                   ], help="Type of commission")
    std_commission_perc = fields.Float(string='Standard Commission Percentage',
                                       help="Standard commission type")
    affiliated_commission_perc = fields.Float(
        string='Affiliated Partner Commission Percentage',
        help="Affiliated partner commission percentage")
    non_affiliated_commission_perc = fields.Float(
        string='Non-Affiliated Partner Commission Percentage',
        help="Non affiliated commission percentage")
    product_based_ids = fields.One2many(
        "product.based.sales.commission", 'sale_commission_id',
        string='Sales commission Exceptions',
        help="Product based sales commission")
    date = fields.Date(string="Date", help="Date")
    description = fields.Char(string="Description", help="Description")
    commission_amount = fields.Float(string="Commission Amount",
                                     help="Commission amount")

    discount_based_ids = fields.One2many(
        "discount.based.sales.commission", 'sale_commission_id',
        string='Commission Rules', help="Discount based")
