# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
        user = self.env.user
        all_accounting = []
        if self.env.ref('base.group_user') in user.groups_id:
            all_invoice = self.env['account.move'].search([
                ('state', 'not in', ['draft', 'cancel'])])
            invoice_count = len(all_invoice)
            all_accounting.append(invoice_count)
            sale_order = self.env['sale.order'].search([
                ('user_id', '=', user.id),
                ('state', 'not in', ['draft', 'sent'])])
            quotations = self.env['sale.order'].search(
                [('user_id', '=', user.id),
                 ('state', '=', 'sent')])
        else:
            all_invoice = self.env['account.move'].search([
                ('partner_id','=', user.partner_id.id),
                ('state', 'not in', ['draft', 'cancel'])])
            invoice_count = len(all_invoice)
            all_accounting.append(invoice_count)
            sale_order = self.env['sale.order'].search([
                ('partner_id', '=', user.partner_id.id),
                ('state', 'not in', ['draft', 'sent'])])
            quotations = self.env['sale.order'].search(
                [('partner_id', '=', user.partner_id.id),
                 ('state', '=', 'sent')])
        all_so = []
        so_count = len(sale_order)
        all_so.append(so_count)
        q_count = len(quotations)
        all_so.append(q_count)
        all_purchase_order = []
        purchase_order = self.env['purchase.order'].search([
            ('partner_id', '=', user.partner_id.id),
            ('state', 'not in', ['draft', 'sent', 'to approve'])])
        rfqs = self.env['purchase.order'].search([
            ('partner_id', '=', user.partner_id.id),
            ('state', 'in', ['sent', 'to approve'])])
        all_purchase_order.append(len(purchase_order))
        all_purchase_order.append(len(rfqs))
        lists = {"so": all_so, "po": all_purchase_order}
        all_ac = 0
        if all_accounting[0] == 0:
            all_ac = 1
        zero_list = [name for name, lst in lists.items() if all(item == 0
                                                              for item in lst)]
        return {
            'all_ac': all_ac,
            'zero_list': zero_list,
            'target': all_so,
            'target_po': all_purchase_order,
            'target_accounting': all_accounting,
        }
