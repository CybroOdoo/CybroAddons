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

from odoo import api, models


class ProductProduct(models.Model):
    """
    Inherited model for Product variants.
    Extends the POS data loading mechanism to include automated manufacturing configurations.
    """
    _inherit = 'product.product'

    @api.model
    def _load_pos_data_fields(self, config):
        """
        Include the automated manufacturing fields in POS data loading.

        :param config: POS configuration record context.
        :return: List of field names loaded to the POS frontend.
        """
        result = super()._load_pos_data_fields(config)
        result.extend(['to_create_mrp', 'create_mrp_done'])
        return result
