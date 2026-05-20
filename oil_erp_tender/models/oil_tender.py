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

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class OilTender(models.Model):
    _name = 'oil.tender'
    _description = 'Master Tender Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    description = fields.Text(string='Work Details', required=True)
    issue_date = fields.Date(string='Issue Date', default=fields.Date.context_today)
    deadline = fields.Datetime(string='Submission Deadline', required=True, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('evaluation', 'Evaluation'),
        ('awarded', 'Awarded')
    ], string='Status', default='draft', tracking=True)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    bid_ids = fields.One2many('oil.tender.bid', 'tender_id', string='Bids Received')
    contract_id = fields.Many2one('oil.contract', string='Created Contract', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Generate a unique sequence reference for new tender records."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('oil.tender') or _('New')
        return super().create(vals_list)

    def action_publish(self):
        """Publish the tender to make it available for bid submissions."""
        self.write({'state': 'published'})

    def action_evaluate(self):
        """Evaluate all received bids and identify the lowest price bid."""
        self.ensure_one()
        if not self.bid_ids:
            return
        # Internal logic for lowest detection
        self.bid_ids.write({'is_lowest': False})
        lowest_bid = self.bid_ids.sorted(key=lambda r: r.bid_price)[0]
        lowest_bid.is_lowest = True
        self.write({'state': 'evaluation'})

    def action_view_contract(self):
        """Open the form view of the contract created from this tender."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Contract',
            'res_model': 'oil.contract',
            'view_mode': 'form',
            'res_id': self.contract_id.id,
            'target': 'current',
        }


class OilTenderBid(models.Model):
    _name = 'oil.tender.bid'
    _description = 'Tender Bid'

    tender_id = fields.Many2one('oil.tender', string='Tender', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True)
    bid_price = fields.Monetary(string='Bid Price', currency_field='currency_id', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    submission_date = fields.Datetime(string='Submission Date', default=fields.Datetime.now, required=True)
    
    is_lowest = fields.Boolean(string='Is Lowest', default=False)
    is_confirmed = fields.Boolean(string='Confirmed', default=False)
    stage_id = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected')])

    @api.model_create_multi
    def create(self, vals_list):
        """Create a bid after verifying the parent tender is in published state."""
        for vals in vals_list:
            tender = self.env['oil.tender'].browse(vals.get('tender_id'))
            if tender.state != 'published':
                raise UserError(_("Bids can only be created when the Tender is in the 'Published' state."))
        return super().create(vals_list)

    def action_confirm_bid(self):
        """Open the confirmation wizard to award the contract to this bid."""
        self.ensure_one()
        return {
            'name': _('Confirm Winning Bid'),
            'type': 'ir.actions.act_window',
            'res_model': 'oil.tender.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bid_id': self.id,
                'default_tender_id': self.tender_id.id,
                'default_partner_id': self.partner_id.id,
                'default_bid_price': self.bid_price,
            }
        }



