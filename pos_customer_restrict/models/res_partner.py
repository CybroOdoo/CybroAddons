# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    """Add available in pos option in res.partner to set restriction for
    customers in POS"""
    _inherit = 'res.partner'

    is_available_in_pos = fields.Boolean(string="Available In POS",
                                         help="Check if you want this customer"
                                              "to appear in the Point of Sale.",
                                         default=False)

    @api.model
    def _load_pos_data_fields(self, config_id):
        return [
            'id', 'name', 'street', 'city', 'state_id', 'country_id', 'vat',
            'lang', 'phone', 'zip', 'mobile', 'email',
            'barcode', 'write_date', 'property_account_position_id',
            'property_product_pricelist', 'parent_name', 'contact_address','is_available_in_pos'
        ]