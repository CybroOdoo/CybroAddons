# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
from odoo import api, models
from odoo.http import request


class ProductProduct(models.Model):
    """
    Inherits the product.template model to extend its functionality.
    """
    _inherit = 'product.template'

    @api.model
    def _get_contextual_price(self, product=None):
        """
        Get the contextual price of a product based on the current pricelist,
        quantity, unit of measure (UOM), and date. If the UOM is not specified
        in the context, it checks the session for a UOM ID.
        """
        self.ensure_one()
        pricelist = self._get_contextual_pricelist()
        quantity = self.env.context.get('quantity', 1.0)
        uom_id = self.env.context.get('uom')
        # Check if uom_id is available in the session
        if not uom_id and request.session.get('uom_id'):
            uom_id = request.session['uom_id']
        date = self.env.context.get('date')
        uom = self.env['uom.uom'].browse(uom_id) if uom_id else self.uom_id
        return pricelist._get_product_price(product or self, quantity, uom=uom,
                                            date=date)
