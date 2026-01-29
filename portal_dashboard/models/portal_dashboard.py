# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class PortalDashboardData(models.Model):
    """Used to set graphs in portal dashboard template"""
    _name = 'portal.dashboard'
    _description = 'To get portal dashboard data'

    @api.model
    def get_dashboard_data(self):
        """To fetch datas of backend documents to show in the portal
        dashboard template depending on count of record"""
        partner, partners = self.env.user.id, self.env.user
        group_id = self.env.ref('base.group_user')
        if group_id in partners.groups_id:
            all_invoice = self.env['account.move'].search_count([
                ('state', 'not in', ['draft', 'cancel']),
                ('move_type', '=', 'out_invoice')])
            all_bills = self.env['account.move'].search_count([
                ('state', 'not in', ['draft', 'cancel']),
                ('move_type', '=', 'in_invoice')])
        else:
            all_invoice = self.env['account.move'].search([
                ('partner_id', '=', partners.partner_id.id),
                ('state', 'not in', ['draft', 'cancel']),
                ('move_type', '=', 'out_invoice')])
            all_bills = self.env['account.move'].search([
                ('partner_id', '=', partners.partner_id.id),
                ('state', 'not in', ['draft', 'cancel']),
                ('move_type', '=', 'out_invoice'),
                ('move_type', '=', 'in_invoice')])
        all_acc = [all_invoice, all_bills]
        sale_order = self.env['sale.order'].search_count([
            ('user_id', '=', partner),
            ('state', 'not in', ['draft', 'sent'])])
        quotations = self.env['sale.order'].search_count([('user_id', '=',
                                                           partner),
                                                          ('state', 'in',
                                                           ['draft', 'sent'])])
        all_so = [sale_order, quotations]
        purchase_order = self.env['purchase.order'].search_count([
            ('user_id', '=', partner),
            ('state', 'not in', ['draft', 'sent', 'to approve'])])
        purchase = self.env['purchase.order'].search_count([
            ('user_id', '=', partner),
            ('state', 'in', ['draft', 'sent', 'to approve'])])
        rfq_count = purchase
        all_purchase_order = [rfq_count, purchase_order]
        return {
            'target': all_so,
            'target_po': all_purchase_order,
            'target_accounting': all_acc
        }
