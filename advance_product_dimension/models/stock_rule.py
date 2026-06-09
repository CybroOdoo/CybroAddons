# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models


class StockRule(models.Model):
    """Propagate dimension values through buy and manufacturing procurements."""
    _inherit = 'stock.rule'

    @staticmethod
    def _get_dimension_procurement_values(values):
        """Return the dimension values that must stay grouped together."""
        return (
            values.get('length', 0.0),
            values.get('width', 0.0),
            values.get('height', 0.0),
            values.get('dimension_qty', 0.0),
            values.get('dimension_method'),
        )

    def _get_procurements_to_merge_groupby(self, procurement):
        """Prevent merges between procurements with different dimensions."""
        return super()._get_procurements_to_merge_groupby(procurement) + self._get_dimension_procurement_values(
            procurement.values
        )

    def _get_custom_move_fields(self):
        """Keep dimension values on stock moves so downstream procurements retain them."""
        fields = super()._get_custom_move_fields()
        fields += ['bom_line_id', 'length', 'width', 'height', 'dimension_qty', 'dimension_method']
        return fields

    def _prepare_mo_vals(self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values, bom):
        """Copy sale dimensions onto manufacturing orders created by procurement."""
        mo_values = super()._prepare_mo_vals(
            product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values, bom
        )
        mo_values.update({
            'length': values.get('length', 0.0),
            'width': values.get('width', 0.0),
            'height': values.get('height', 0.0),
            'dimension_qty': values.get('dimension_qty', 0.0),
            'dimension_method': values.get('dimension_method', 'length_width_height'),
        })
        return mo_values
