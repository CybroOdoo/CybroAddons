# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abbas P (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    """Inherit the sale.order model for supering the action confirm."""
    _inherit = "sale.order"

    is_membership_extension = fields.Boolean(
        string='Is Membership Extension',
        default=False,
        help='If True, this sale order is for extending an existing membership and should not create a new membership record.'
    )

    def action_confirm(self):
        """Membership created directly from sale order confirmed - FIXED VERSION"""

        if self.is_membership_extension:
            # Log that this is an extension order
            self.message_post(
                body=_('This is a membership extension order. No new membership record will be created.'),
                message_type='notification'
            )
            # Call super but skip membership creation logic
            return super().action_confirm()

        # Original logic for NEW memberships only
        product = self.env['product.product'].search([
            ('membership_date_from', '!=', False),
            ('id', 'in', self.order_line.product_id.ids)
        ])

        for record in product:
            membership = self.env['gym.membership'].create({
                'member_id': self.partner_id.id,
                'membership_date_from': record.membership_date_from,
                'membership_scheme_id': record.id,
                'sale_order_id': self.id,
                'state': 'confirm',
            })
            self.partner_id.is_gym_member = True

        return super().action_confirm()