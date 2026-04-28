# -*- coding: utf-8 -*-

#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: K Sai Saran Varma (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Inherited product.template"""
    _inherit = 'product.template'

    is_age_restrict = fields.Boolean(string="Is Age Restricted",
                                     help="By enabling age restrictions on a "
                                          "product")

class ProductProduct(models.Model):
        """Inherited product.product"""
        _inherit = 'product.product'

        is_age_restrict = fields.Boolean(
            related="product_tmpl_id.is_age_restrict",
            store=True,
            readonly=False
        )

        @api.model
        def _load_pos_data_fields(self, config_id):
            """Extends the result of the _load_pos_data_fields method by appending
              the 'is_age_restrict' field."""
            result = super()._load_pos_data_fields(config_id)
            result.append('is_age_restrict')
            return result
