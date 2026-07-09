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
from odoo import api, fields, models, _


class AssetModify(models.TransientModel):
    _name = 'asset.modify'
    _description = 'Modify Asset'

    name = fields.Text(string='Reason', required=True)
    method_number = fields.Integer(string='Number of Depreciations', required=True)
    method_period = fields.Integer(string='Period Length')
    method_end = fields.Date(string='Ending date')
    # Populated from the active asset in ``default_get``; the form uses it in
    # ``invisible=`` expressions to toggle method_end / method_number.
    asset_method_time = fields.Char(string='Asset Method Time', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        asset_id = self.env.context.get('active_id')
        asset = self.env['account.asset.asset'].browse(asset_id)
        if 'name' in fields_list:
            res.update({'name': asset.name})
        if 'method_number' in fields_list and asset.method_time == 'number':
            res.update({'method_number': asset.method_number})
        if 'method_period' in fields_list:
            res.update({'method_period': asset.method_period})
        if 'method_end' in fields_list and asset.method_time == 'end':
            res.update({'method_end': asset.method_end})
        if asset:
            res['asset_method_time'] = asset.method_time
        return res

    def modify(self):
        """ Modifies the duration of asset for calculating depreciation
        and maintains the history of old values, in the chatter.
        """
        asset_id = self.env.context.get('active_id', False)
        asset = self.env['account.asset.asset'].browse(asset_id)
        asset_vals = {
            'method_number': self.method_number,
            'method_period': self.method_period,
            'method_end': self.method_end,
        }
        asset.write(asset_vals)
        asset.compute_depreciation_board()
        asset.message_post(body=self.name or _('Depreciation board modified'))
        return {'type': 'ir.actions.act_window_close'}
