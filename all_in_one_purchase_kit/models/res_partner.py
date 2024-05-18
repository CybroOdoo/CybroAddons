# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
    """Inheriting res partner to add fields and methods"""
    _inherit = 'res.partner'

    default_discount = fields.Float(string='Discount(%)',
                                    help="Enter discount amount in %")
    _sql_constraints = [
        (
            "maximum_discount",
            "CHECK (discount <= 100.0)",
            "Discount must be lower than 100%.",
        )
    ]

    @api.model
    def get_vendor_po(self):
        """Get purchase order of vendors"""
        count_dict = {
            count['name']: count['purchase_order_count']
            for count in self.search_read(
                [], ['name', 'purchase_order_count'],
                order='purchase_order_count')
            if count['purchase_order_count'] > 0
        }
        return {'purchase_order_count': {key: val for key, val in sorted(
            count_dict.items(), key=lambda ele: ele[1], reverse=True)}}
