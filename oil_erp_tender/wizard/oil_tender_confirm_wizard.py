# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

class OilTenderConfirmWizard(models.TransientModel):
    _name = 'oil.tender.confirm.wizard'
    _description = 'Confirm Tender Bid'

    bid_id = fields.Many2one('oil.tender.bid', string='Selected Bid', required=True)
    tender_id = fields.Many2one('oil.tender', string='Tender', required=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    bid_price = fields.Monetary(string='Bid Price', currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    def action_confirm(self):
        """Create a contract from the winning bid, award the tender, and mark all other bids as rejected."""
        self.ensure_one()
        tender = self.tender_id
        winning_bid = self.bid_id
        
        # 1. Create Contract
        contract = self.env['oil.contract'].create({
            'tender_id': tender.id,
            'vendor_id': winning_bid.partner_id.id,
            'amount': winning_bid.bid_price,
            'project_id': tender.project_id.id,
            'select_type': 'project',
            'description': tender.description,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(), # Placeholder
        })
        
        # 2. Update Tender
        tender.write({
            'state': 'awarded',
            'contract_id': contract.id,
        })
        
        # 3. Update Bids (No Deletion)
        tender.bid_ids.write({'is_confirmed': False})
        for bid in tender.bid_ids:
            if bid.id == winning_bid.id:
                bid.write({
                    'is_confirmed': True,
                    'stage_id': 'confirmed',
                })
            else:
                bid.write({
                    'is_confirmed': False,
                    'stage_id': 'rejected',
                    'is_lowest': False,
                })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract Created',
            'res_model': 'oil.contract',
            'view_mode': 'form',
            'res_id': contract.id,
            'target': 'current',
        }

