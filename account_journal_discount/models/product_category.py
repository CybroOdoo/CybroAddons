# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vivek @ cybrosys,(odoo@cybrosys.com)
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
from odoo import models, fields


class ProductCategory(models.Model):
    """Extending this model is required to add new fields for setting up
        vendor and customer discount accounts.
    """
    _inherit = "product.category"

    ACCOUNT_DOMAIN = "['&', '&', '&', ('deprecated', '=', False), " \
                     "('account_type', 'not in', ('asset_receivable'," \
                     "'liability_payable','asset_cash'," \
                     "'liability_credit_card')), ('company_id', '=', " \
                     "current_company_id), ('is_off_balance', '=', False)]"
    # This account will be used vendor discount
    vendor_account_discount_id = fields.Many2one('account.account',
                                                 help="account for setting up "
                                                      "vendor discounts",
                                                 company_dependent=True,
                                                 string=
                                                 "Vendor Discount Account",
                                                 domain=ACCOUNT_DOMAIN)
    # This account will be used customer discount
    customer_account_discount_id = fields.Many2one('account.account',
                                                   help="account for setting up"
                                                        " customer discounts",
                                                   company_dependent=True,
                                                   string=
                                                   "Customer Discount Account",
                                                   domain=ACCOUNT_DOMAIN)
