# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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


class ProductTemplate(models.Model):
    """new product type is added for appointment booking"""
    _inherit = "product.template"

    detailed_type = fields.Selection(selection_add=[
        ('booking_fees', 'Booking Fees'),
    ], help="Added new detailed type for appointment booking",
        ondelete={'booking_fees': 'set service'})

    def _detailed_type_mapping(self):
        """Added a new product type for appointment booking"""
        type_mapping = super()._detailed_type_mapping()
        type_mapping['booking_fees'] = 'service'
        return type_mapping
