# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
######################################################################################
from odoo import api, fields, models


class TextileReport(models.TransientModel):
    """Create a new model for report wizard"""
    _name = 'textile.report'
    _description = 'Textile Report'

    type = fields.Selection([('customer', 'Customer'), ('vendor', 'Vendor')],
                            string="Type", default="customer",
                            help="Type of Textile Report")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="Customer")
    vendor_id = fields.Many2one('res.partner', string="Vendor",
                                help="Vendor")
    date_begin = fields.Date(string='From Date', help="From Date")
    date_end = fields.Date(string='To Date', help="End Date")
    textile_customer_ids = fields.Many2many(
        'res.partner', compute='_compute_textile_partners', store=False
    )

    textile_vendor_ids = fields.Many2many(
        'res.partner', compute='_compute_textile_partners', store=False
    )

    @api.depends('type')
    def _compute_textile_partners(self):
        for rec in self:
            if rec.type == 'customer':
                rec.textile_customer_ids = self.env['sale.order'].search([
                    ('is_textile_sale_order', '=', True)
                ]).mapped('partner_id')
                rec.textile_vendor_ids = False

            else:
                rec.textile_vendor_ids = self.env['purchase.order'].search([
                    ('is_textile_purchase_order', '=', True)
                ]).mapped('partner_id')
                rec.textile_customer_ids = False

    def action_customer_vendor_report(self):
        """To print reports"""
        customer = []
        vendor = []
        sale_order = None
        purchase_order = None

        if self.customer_id:
            # Build a separate domain for sale orders
            sale_domain = [('is_textile_sale_order', '=', True),
                           ('partner_id', '=', self.customer_id.id)]
            if self.date_begin:
                sale_domain.append(('date_order', '>=', self.date_begin))
            if self.date_end:
                sale_domain.append(('date_order', '<=', self.date_end))
            sale_order = self.env['sale.order'].sudo().search(sale_domain)

        if self.vendor_id:
            # Build a separate domain for purchase orders
            purchase_domain = [('is_textile_purchase_order', '=', True),
                               ('partner_id', '=', self.vendor_id.id)]
            if self.date_begin:
                purchase_domain.append(('date_order', '>=', self.date_begin))
            if self.date_end:
                purchase_domain.append(('date_order', '<=', self.date_end))
            purchase_order = self.env['purchase.order'].sudo().search(
                purchase_domain)

        if purchase_order:
            vendor = [{
                'vendor': rec.partner_id.name,
                'purchase': rec.name,
                'create_date': rec.date_order.strftime('%Y-%m-%d'),
                'amount': rec.amount_total,
                'status': rec.state,
            } for rec in purchase_order]
        if sale_order:
            customer = [{
                'customer': rec.partner_id.name,
                'sale': rec.name,
                'create_date': rec.date_order.strftime('%Y-%m-%d'),
                'amount': rec.amount_total,
                'status': rec.state,
            } for rec in sale_order]
        data = {
            'type': self.type,
            'customer': self.customer_id.name,
            'vendor': self.vendor_id.name,
            'date_begin': self.date_begin,
            'date_end': self.date_end,
            'customer_details': customer,
            'vendor_details': vendor,
        }
        report = self.env.ref(
            'textile_management.action_textile_report')
        return report.report_action(None, data=data)