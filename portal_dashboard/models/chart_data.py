# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Megha A P (odoo@cybrosys.com)
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
    """Used to set graphs in portal dashboard template"""
    _name = 'portal.dashboard.data'
    _description = 'To get portal dashboard data'

    @api.model
    def datafetch(self):
        """To fetch datas of backend documents to show in the portal
        dashboard template depending on count of record"""

        partner = self.env.user.id
        partners = self.env.user
        group_id = self.env.ref('base.group_user')
        all_accounting = []
        if group_id in partners.groups_id:

            all_invoice = self.env['account.move'].search([
                ('state', 'not in', ['draft', 'cancel'])
            ])

            invoice_count = len(all_invoice)
            all_accounting.append(invoice_count)
        else:
            all_invoice = self.env['account.move'].search([
                ('partner_id','=', partners.partner_id.id),
                ('state', 'not in', ['draft', 'cancel'])
            ])

            invoice_count = len(all_invoice)
            all_accounting.append(invoice_count)

        all_so = []
        sale_order = self.env['sale.order'].search([
            ('user_id', '=', partner),
            ('state', 'not in', ['draft', 'sent'])])

        quotations = self.env['sale.order'].search([('user_id', '=', partner),
                                                    ('state', 'in', ['sent'])
                                                    ])

        so_count = len(sale_order)
        all_so.append(so_count)
        q_count = len(quotations)
        all_so.append(q_count)

        all_purchase_order = []
        purchase_order = self.env['purchase.order'].search([
            ('user_id', '=', partner),
            ('state', 'not in', ['draft', 'sent', 'to approve'])
        ])
        rfqs = self.env['purchase.order'].search([
            ('user_id', '=', partner),
            ('state', 'in', ['sent', 'to approve'])
        ])

        po_count = len(purchase_order)
        all_purchase_order.append(po_count)
        rfq_count = len(rfqs)
        all_purchase_order.append(rfq_count)

        return {
            'target': all_so,
            'target_po': all_purchase_order,
            'target_accounting': all_accounting
        }
