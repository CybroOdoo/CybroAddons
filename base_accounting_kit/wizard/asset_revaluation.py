# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class AssetRevaluation(models.TransientModel):
    """Wizard to increase an asset's gross value (improvement / revaluation)
    and re-spread the remaining depreciation."""
    _name = 'asset.revaluation'
    _description = 'Asset Revaluation'

    asset_id = fields.Many2one('account.asset.asset', string='Asset',
                               required=True)
    currency_id = fields.Many2one(related='asset_id.currency_id')
    value_increase = fields.Monetary(string='Value Increase', required=True,
                                     help="Amount added to the asset's gross value.")
    date = fields.Date(string='Date', required=True,
                       default=fields.Date.context_today)
    account_id = fields.Many2one(
        'account.account', string='Counterpart Account', required=True,
        help="Credited by the revaluation entry (the asset account is debited).")

    def action_revaluate(self):
        self.ensure_one()
        self.asset_id._revaluate(self.value_increase, self.date,
                                 self.account_id)
        return {'type': 'ir.actions.act_window_close'}
