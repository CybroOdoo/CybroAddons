# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

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
        """Compute textile customers and vendors based on report type"""
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
        """Generate textile customer or vendor report"""
        customer = []
        vendor = []
        domain = []
        sale_order = None
        purchase_order = None
        if self.date_begin or self.date_end:
            domain.extend([('date_order', '>=', self.date_begin),
                           ('date_order', '<=', self.date_end),])
        if self.customer_id:
            domain.append(('partner_id', '=', self.customer_id.id))
            domain.append(('is_textile_sale_order', '=', True))
            sale_order = self.env['sale.order'].sudo().search(domain)
        if self.vendor_id:
            domain.append(('partner_id', '=', self.vendor_id.id))
            domain.append(('is_textile_purchase_order', '=', True))
            purchase_order = self.env['purchase.order'].sudo().search(domain)
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
