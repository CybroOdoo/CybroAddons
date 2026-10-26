# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.info)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models


class ProductTemplate(models.Model):
    """
    Inherits the product.template model to extend its functionality.
    """
    _inherit = 'product.template'

    def _get_available_uoms(self):
        """
        Extend available UOMs to include all active units related to the product's UOM
        category / relative UOM, matching the options presented in the website shop dropdown.
        """
        res = super()._get_available_uoms()
        if not self:
            return res
        self.ensure_one()
        root_uom = self.uom_id.relative_uom_id or self.uom_id
        return (res | root_uom | root_uom.related_uom_ids | self.uom_ids).filtered('active')
