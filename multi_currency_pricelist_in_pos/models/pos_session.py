# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#############################################################################
from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_product_pricelist(self):
        """Load pricelist currency information into the POS session data."""
        result = super()._loader_params_product_pricelist()
        fields = result["search_params"]["fields"]
        if "currency_id" not in fields:
            fields.append("currency_id")
        return result

    def _pos_data_process(self, loaded_data):
        """Prepare currency data required for multi-currency pricelists in POS."""
        super()._pos_data_process(loaded_data)
        loaded_data["multi_currency_pricelist_currencies"] = []
        if not (self.config_id.use_pricelist and self.config_id.enable_multi_currency_pricelist):
            return
        currency_ids = (
            self.config_id.available_pricelist_ids.mapped("currency_id")
            | self.config_id.pricelist_id.currency_id
            | self.config_id.currency_id
            | self.company_id.currency_id
        ).ids
        loaded_data["multi_currency_pricelist_currencies"] = self.env["res.currency"].search_read(
            [("id", "in", currency_ids)],
            ["name", "symbol", "position", "rounding", "rate", "decimal_places"],
        )
