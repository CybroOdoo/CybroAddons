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
from odoo import fields, models, _


class AssetDispose(models.TransientModel):
    """Wizard to sell or scrap an asset, booking the gain/loss."""
    _name = 'asset.dispose'
    _description = 'Sell or Dispose Asset'

    asset_id = fields.Many2one('account.asset.asset', string='Asset',
                               required=True)
    currency_id = fields.Many2one(related='asset_id.currency_id')
    disposal_type = fields.Selection(
        [('scrap', 'Scrap'), ('sale', 'Sale')],
        string='Disposal Type', required=True, default='scrap')
    date = fields.Date(string='Disposal Date', required=True,
                       default=fields.Date.context_today)
    sale_value = fields.Monetary(string='Sale Value',
                                 help="Proceeds received from the sale.")
    sale_account_id = fields.Many2one(
        'account.account', string='Proceeds Account',
        help="Account debited with the sale proceeds (e.g. a bank or "
             "receivable account).")

    def action_dispose(self):
        self.ensure_one()
        sale_value = self.sale_value if self.disposal_type == 'sale' else 0.0
        sale_account = (self.sale_account_id
                        if self.disposal_type == 'sale' else False)
        move = self.asset_id._dispose(
            self.date, sale_value=sale_value, sale_account=sale_account)
        return {
            'name': _('Disposal Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': move.id,
            'target': 'current',
        }
