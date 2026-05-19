# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models ,api
from odoo.tools import _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    """Inherited the model product Template for adding a field."""
    _inherit = 'product.template'

    is_gym_product = fields.Boolean(string='Gym Product',
                                    help='This help to define the product '
                                         'whether'
                                         'it is gym product')
    membership = fields.Boolean(help='Check if the product is eligible for membership.')
    membership_date_from = fields.Date(string='Membership Start Date',
                                           help='Date from which membership becomes active.')
    membership_date_to = fields.Date(string='Membership End Date',
                                         help='Date until which membership remains active.')

    @api.constrains("membership_date_from", "membership_date_to")
    def _check_membership_plan_dates(self):
        """Ensure membership end date is not earlier than start date."""
        for rec in self:
            if rec.membership_date_from and rec.membership_date_to:
                if rec.membership_date_to < rec.membership_date_from:
                    raise ValidationError(
                        _("Error! Ending Date cannot be set before Beginning Date.")
                    )
