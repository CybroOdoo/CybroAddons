# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: JANISH BABU (<https://www.cybrosys.com>)
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
from odoo import fields, models


class ResPartner(models.Model):
    """Inherited res partner model"""
    _inherit = 'res.partner'

    is_active_subscription = fields.Boolean(string="Active Subscription",
                                            default=False,
                                            help='Is Subscription is active')
    subscription_product_line_ids = fields.One2many(
        'subscription.package.product.line', 'res_partner_id',
        ondelete='restrict', string='Products Line',
        help='Subscription product')

    def _valid_field_parameter(self, field, name):
        """
        Validate field parameters, allowing custom handling for 'ondelete'
        """
        if name == 'ondelete':
            return True
        return super(ResPartner,
                     self)._valid_field_parameter(field, name)
