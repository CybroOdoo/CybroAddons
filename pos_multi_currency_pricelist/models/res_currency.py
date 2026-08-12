# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import models


class ResCurrency(models.Model):
    """Extend currency loading for POS multi-currency pricelists."""
    _inherit = "res.currency"

    def _load_pos_data_domain(self, data):
        """Limit loaded currencies to those used by the POS configuration.
        When multi-currency pricelists are enabled, only the currencies required
        by the POS, its available pricelists, and the company are loaded.
        """
        domain = super()._load_pos_data_domain(data)
        config = self.env["pos.config"].browse(data["pos.config"]["data"][0]["id"])
        if not (config.use_pricelist and config.enable_multi_currency_pricelist):
            return domain

        currency_ids = (
            config.available_pricelist_ids.mapped("currency_id")
            | config.pricelist_id.currency_id
            | config.currency_id
            | config.company_id.currency_id
        ).ids
        return [("id", "in", currency_ids)]
