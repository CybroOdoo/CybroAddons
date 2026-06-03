# -*- coding: utf-8 -*-
###############################################################################
#
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
###############################################################################
from odoo import api, fields, models


class TenderBidding(models.Model):
    """ Class for holding tender bidding details. """
    _name = "tender.bidding"
    _inherit = 'mail.thread'
    _description = 'Tender Bidding'

    name = fields.Char(string="Bidding Reference", help='Bidding Reference', readonly=True)
    vendor_id = fields.Many2one('res.partner', string="Vendor", help="name of the vendor")
    tender_id = fields.Many2one('tender.management', string="Tender", help="chosen tender")
    bidding_state = fields.Selection(
        [('pre_qualification', 'PRE QUALIFICATION'), ('bid', 'BID'), ('bid_close', 'BID CLOSE'),
         ('won', 'WON'), ('lost', 'LOST')],default='pre_qualification', help="bidding stages", tracking=True)
    bidding_date = fields.Date(string="Date", help="tender bidding date")
    vendor_attachments_ids = fields.Many2many('ir.attachment', string='Attachments',help='vendor attachments for the '
                                                                                         'tender')
    tender_bid_products_ids = fields.One2many('tender.bidding.product.lines', 'tender_bidding_id',help='tender '
                                                                                                       'products for '
                                                                                                       'bidding')
    total_bidding_amount = fields.Float(string="Total Amount", help="bidding total",
                                        compute="_compute_total_bidding_amount", store=True)
    qualification_stage = fields.Selection(
        [('initial', 'Initial'), ('qualified', 'Qualified'), ('disqualified', 'Disqualified')],
        help="bid qualified or not ?", default='initial', tracking=True)
    legit_bid = fields.Boolean(string="Legit Bid", help="is bid legit or not ?", compute="_compute_legit_bid",
                               store=True)
    edit_request = fields.Boolean(string="has vendor requested for bid edit", default=False,help='edit existing '
                                                                                                 'tender bid')
    vendor_rank = fields.Integer(string="Vendor Rank", help="Rank of the vendor", compute="_compute_vendor_rank",
                                 store=True)

    @api.depends('tender_id', 'total_bidding_amount', 'qualification_stage')
    def _compute_vendor_rank(self):
        """Function to compute vendor rank based on total bidding amount."""
        for rec in self:
            rec.vendor_rank = 0
            if rec.qualification_stage == 'qualified':
                all_bids = self.search(
                    [('tender_id', '=', rec.tender_id.id), ('qualification_stage', '=', 'qualified')],
                    order='total_bidding_amount asc')
                rec.vendor_rank = all_bids.ids.index(rec.id) + 1

    @api.depends('tender_bid_products_ids')
    def _compute_total_bidding_amount(self):
        """Function to compute total bidding amount"""
        for rec in self:
            rec.total_bidding_amount = sum(rec.tender_bid_products_ids.mapped('product_total'))

    @api.depends('tender_bid_products_ids')
    def _compute_legit_bid(self):
        """Function for computing legit bid based on product price."""
        for rec in self:
            rec.legit_bid = not any(product_price == 0 for product_price in
                                    rec.tender_bid_products_ids.filtered(lambda x: not x.display_type).mapped(
                                        'product_price'))

    def write(self, vals):
        """Override write method to ensure rank recalculation."""
        res = super(TenderBidding, self).write(vals)
        if 'total_bidding_amount' in vals or 'qualification_stage' in vals or 'tender_id' in vals:
            # Recompute ranks for all related records
            tender_ids = self.mapped('tender_id').ids
            self.env['tender.bidding'].search([('tender_id', 'in', tender_ids)])._compute_vendor_rank()
        return res

    @api.model
    def create(self, vals):
        """Function to create sequence number for tender bidding and ensure rank recalculation."""
        vals['name'] = self.env['ir.sequence'].next_by_code('tender.bidding')
        new_record = super(TenderBidding, self).create(vals)
        # Recompute ranks for all related records
        tender_id = vals.get('tender_id')
        if tender_id:
            self.env['tender.bidding'].search([('tender_id', '=', tender_id)])._compute_vendor_rank()
        return new_record

    def action_approve_edit_request(self):
        """Function to approve bid edit request"""
        self.bidding_state = 'bid'
        self.edit_request = False
        template = self.env.ref('advanced_tender_management.edit_request_approved_template')
        template.send_mail(self.id, force_send=True)

    def action_qualify(self):
        """Function to qualify bid for selection"""
        self.qualification_stage = 'qualified'
        template = self.env.ref('advanced_tender_management.bidding_qualified_template')
        template.send_mail(self.id, force_send=True)

    def action_disqualify(self):
        """Function to disqualify bid from further procedures"""
        self.qualification_stage = 'disqualified'
        template = self.env.ref('advanced_tender_management.bidding_disqualified_template')
        template.send_mail(self.id, force_send=True)
