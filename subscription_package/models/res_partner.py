# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    """Inherited res partner model"""
    _inherit = 'res.partner'

    is_active_subscription = fields.Boolean(string="Active Subscription",
                                            default=False,
                                            help='Is Subscription is active')
    is_subscription_customer = fields.Boolean(
        string="Subscription Customer",
        default=False,
        help="Identifies if the partner is a subscription customer")
    subscription_product_line_ids = fields.One2many(
        'subscription.package.product.line', 'res_partner_id',
        string='Products Line',
        help='Subscription product')
