# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Henna Mehjabin (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, models


class ChartData(models.Model):
    """Provides analytics data for the portal dashboard charts."""
    _name = 'portal.dashboard.data'
    _description = 'Portal Dashboard Analytics Data'

    @api.model
    def datafetch(self):
        """Fetch counts of backend records to display in portal dashboard charts
        for sales, purchases, and accounting."""
        user = self.env.user
        partner = user.partner_id
        is_internal = user.has_group('base.group_user')

        SaleOrder = self.env['sale.order'].sudo()
        PurchaseOrder = self.env['purchase.order'].sudo()
        AccountMove = self.env['account.move']

        if is_internal:
            commercial_partner = partner.commercial_partner_id.id
            internal_partner_domain = ('partner_id', 'child_of', [commercial_partner])

            # Sales Analysis for internal salesperson or partner
            so_count = SaleOrder.search_count([
                '|', internal_partner_domain,
                ('user_id', '=', user.id),
                ('state', 'not in', ['draft', 'sent', 'cancel']),
            ])
            q_count = SaleOrder.search_count([
                '|', internal_partner_domain,
                ('user_id', '=', user.id),
                ('state', 'in', ['draft', 'sent']),
            ])

            # Purchase Analysis for internal purchaser or partner
            po_count = PurchaseOrder.search_count([
                '|', internal_partner_domain,
                ('user_id', '=', user.id),
                ('state', 'not in', ['draft', 'sent', 'to approve', 'cancel']),
            ])
            rfq_count = PurchaseOrder.search_count([
                '|', internal_partner_domain,
                ('user_id', '=', user.id),
                ('state', 'in', ['draft', 'sent', 'to approve']),
            ])

            # Accounting Analysis: invoices (Customer or Salesperson) vs vendor bills (Vendor)
            company_domain = [('company_id', '=', self.env.company.id)] if self.env.company else []
            invoice_count = AccountMove.search_count(company_domain + [
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', 'not in', ['draft', 'cancel']),
                '|',
                internal_partner_domain,
                ('invoice_user_id', '=', user.id),
            ]) if AccountMove.has_access('read') else 0
            bill_count = AccountMove.search_count(company_domain + [
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', 'not in', ['draft', 'cancel']),
                internal_partner_domain,
            ]) if AccountMove.has_access('read') else 0
        else:
            # Domain for portal customer / vendor partner
            partner_domain = [('partner_id', 'child_of', [partner.commercial_partner_id.id])]

            # Sales Analysis: confirmed sale orders vs quotations (sent/cancel)
            so_count = SaleOrder.search_count(partner_domain + [
                ('state', 'in', ['sale', 'done']),
            ])
            q_count = SaleOrder.search_count(partner_domain + [
                ('state', 'in', ['sent', 'cancel']),
            ])

            # Purchase Analysis: purchase orders vs RFQs (sent/to approve)
            po_count = PurchaseOrder.search_count(partner_domain + [
                ('state', 'in', ['purchase', 'done']),
            ])
            rfq_count = PurchaseOrder.search_count(partner_domain + [
                ('state', 'in', ['sent', 'to approve']),
            ])

            # Accounting Analysis: customer invoices vs vendor bills
            invoice_count = AccountMove.search_count(partner_domain + [
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', 'not in', ['draft', 'cancel']),
            ]) if AccountMove.has_access('read') else 0
            bill_count = AccountMove.search_count(partner_domain + [
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', 'not in', ['draft', 'cancel']),
            ]) if AccountMove.has_access('read') else 0

        return {
            'target': [so_count, q_count],
            'target_po': [po_count, rfq_count],
            'target_accounting': [invoice_count, bill_count],
        }
