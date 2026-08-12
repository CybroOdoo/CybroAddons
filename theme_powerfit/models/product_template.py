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
"""Extension of product.template with Gym Plan fields for PowerFit theme."""

from odoo import fields, models

# Category order used for website display sorting
_CATEGORY_ORDER = {'basic': 0, 'standard': 1, 'premium': 2}


class ProductTemplate(models.Model):
    """Extend product.template with Gym Plan attributes for the PowerFit website."""

    _inherit = 'product.template'

    # ─── Gym Plan Toggle ──────────────────────────────────────────────────────
    is_gym_plan = fields.Boolean(
        string='Gym Plan',
        default=False,
        help='Enable to mark this product as a Gym Membership Plan displayed '
             'on the PowerFit website Membership page.',
    )

    # ─── Plan Category ────────────────────────────────────────────────────────
    gym_plan_category = fields.Selection(
        selection=[
            ('basic', 'Basic'),
            ('standard', 'Standard'),
            ('premium', 'Premium'),
        ],
        string='Plan Category',
        help='Determines the card position and styling on the Membership page.',
    )

    # ─── Plan Description ─────────────────────────────────────────────────────
    gym_plan_description = fields.Char(
        string='Plan Description',
        help='Short tagline shown below the price on the Membership card '
             '(e.g. "Perfect for beginners").',
    )

    # ─── Membership Details ──────────────────────────────────────────────────
    membership_details = fields.Text(
        string='Membership Details',
        help='List of membership features/details displayed on the Membership card (one per line).',
    )

