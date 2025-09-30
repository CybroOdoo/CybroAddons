# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api,models

class PortalDashboardData(models.AbstractModel):
    _name = 'portal.dashboard.data'

    @api.model
    def datafetch(self):
        """To fetch data for portal dashboard"""
        partner_id = self.env.user.id
        user = self.env.user
        group_user = self.env.ref('base.group_user')

        if group_user in user.groups_id:
            all_invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', 'not in', ['draft', 'cancel']),
            ])
            invoice_count = len(all_invoices)

            all_bills = self.env['account.move'].search([
                ('move_type', '=', 'in_invoice'),
                ('state', 'not in', ['draft', 'cancel']),
            ])
            bill_count = len(all_bills)

        else:
            all_invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('partner_id', '=', user.partner_id.id),
                ('state', 'not in', ['draft', 'cancel']),
            ])
            invoice_count = len(all_invoices)

            all_bills = self.env['account.move'].search([
                ('move_type', '=', 'in_invoice'),
                ('partner_id', '=', user.partner_id.id),
                ('state', 'not in', ['draft', 'cancel']),
            ])
            bill_count = len(all_bills)

        all_accounting = [invoice_count, bill_count]  # ✅ both values added

        # Sales data
        quotations = self.env['sale.order'].search([
            ('user_id', '=', partner_id), ('state', 'in', ['sent'])
        ])
        q_count = len(quotations)

        sale_orders = self.env['sale.order'].search([
            ('user_id', '=', partner_id), ('state', 'not in', ['draft', 'sent'])
        ])
        so_count = len(sale_orders)

        all_so = [so_count, q_count]

        # Purchase data
        rfqs = self.env['purchase.order'].search([
            ('user_id', '=', partner_id), ('state', 'in', ['sent', 'to approve'])
        ])
        rfq_count = len(rfqs)

        purchase_orders = self.env['purchase.order'].search([
            ('user_id', '=', partner_id), ('state', 'not in', ['draft', 'sent', 'to approve'])
        ])
        po_count = len(purchase_orders)

        all_purchase_order = [po_count, rfq_count]

        return {
            'target': all_so,
            'target_po': all_purchase_order,
            'target_accounting': all_accounting,
        }
