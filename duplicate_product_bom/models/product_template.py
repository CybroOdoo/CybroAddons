# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
from odoo import models


class ProductTemplate(models.Model):
    """
    Inherits from 'product.template' model and extends the 'copy' method.
    """
    _inherit = 'product.template'

    def copy(self, default=None):
        """
            Overrides the default 'copy' method to copy BOM information along
             with the template.
            Args:
                default (dict, optional): Default values for the new record
                being created.
            Returns:
                ProductTemplate: A new instance of the product template with
                 copied BOM information.
            """
        result = super().copy(default)
        for bom in self.bom_ids:
            bom.copy({
                'product_tmpl_id': result.id,
            })
        return result
