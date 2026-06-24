# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhu Shankar E (odoo@cybrosys.com)
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
##############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings', 'pos.load.mixin']

    # Not related anymore
    currency_ids = fields.Many2many(
        'res.currency',
        string="Currencies",
        help="The list of currencies supported by this POS configuration."
    )

    enable_currency = fields.Boolean(
        string="Enable Currency",
        help="Enable multicurrency support in the POS."
    )

    # ---------------------------------------------------------
    # LOAD VALUES FROM pos.config INTO THE SETTINGS SCREEN
    # ---------------------------------------------------------
    @api.model
    def get_values(self):
        res = super().get_values()
        pos_config = self.env['pos.config'].search([], limit=1)

        res.update({
            'enable_currency': pos_config.enable_multicurrency,
            'currency_ids': [(6, 0, pos_config.currency_ids.ids)],
        })
        return res

    # ---------------------------------------------------------
    # SAVE VALUES FROM SETTINGS INTO pos.config
    # ---------------------------------------------------------
    def set_values(self):
        super().set_values()
        pos_config = self.env['pos.config'].search([], limit=1)

        pos_config.enable_multicurrency = self.enable_currency
        pos_config.currency_ids = [(6, 0, self.currency_ids.ids)]

    # ---------------------------------------------------------
    # LOADING FIELDS TO POS (unchanged)
    # ---------------------------------------------------------
    def _load_pos_data_search_read(self, data, config):
        read_data = super()._load_pos_data_search_read(data, config)
        return read_data
