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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Extend POS settings with multi-currency pricelist configuration."""
    _inherit = "res.config.settings"

    pos_enable_multi_currency_pricelist = fields.Boolean(
        related="pos_config_id.enable_multi_currency_pricelist",
        readonly=False,
    )

    @api.depends(
        "pos_use_pricelist",
        "pos_config_id",
        "pos_journal_id",
        "pos_enable_multi_currency_pricelist",
    )
    def _compute_pos_pricelist_id(self):
        """Compute the default and available POS pricelists."""
        for res_config in self:
            currency_id = (
                res_config.pos_journal_id.currency_id.id
                if res_config.pos_journal_id.currency_id
                else res_config.pos_config_id.company_id.currency_id.id
            )
            pricelists_in_current_currency = self.env["product.pricelist"].search(
                [
                    *self.env["product.pricelist"]._check_company_domain(res_config.pos_config_id.company_id),
                    ("currency_id", "=", currency_id),
                ]
            )
            if not res_config.pos_use_pricelist:
                res_config.pos_pricelist_id = False
                res_config.pos_available_pricelist_ids = res_config.pos_config_id.available_pricelist_ids
            elif res_config.pos_enable_multi_currency_pricelist:
                res_config.pos_available_pricelist_ids = res_config.pos_config_id.available_pricelist_ids
                res_config.pos_pricelist_id = res_config.pos_config_id.pricelist_id
            else:
                if any(pricelist.currency_id.id != currency_id for pricelist in res_config.pos_available_pricelist_ids):
                    res_config.pos_available_pricelist_ids = pricelists_in_current_currency
                    res_config.pos_pricelist_id = pricelists_in_current_currency[:1]
                else:
                    res_config.pos_available_pricelist_ids = res_config.pos_config_id.available_pricelist_ids
                    res_config.pos_pricelist_id = res_config.pos_config_id.pricelist_id
