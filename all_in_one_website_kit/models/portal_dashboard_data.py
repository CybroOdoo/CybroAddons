# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models


class PortalDashboardData(models.Model):
    """Used to set graphs in portal dashboard template"""
    _name = 'portal.dashboard.data'
    _description = 'To get portal dashboard data'

    @api.model
    def datafetch(self):
        """To fetch datas of backend documents to show in the portal
        dashboard template depending on count of record"""
        user = self.env.user
        group_id = self.env.ref('base.group_user')
        if group_id in user.groups_id:
            all_invoice = self.env['account.move'].search_count([
                ('state', 'not in', ['draft', 'cancel'])])
            all_accounting = [all_invoice]
        else:
            all_invoice = self.env['account.move'].search_count([
                ('partner_id', '=', user.partner_id.id),
                ('state', 'not in', ['draft', 'cancel'])])
            all_accounting = [all_invoice]
        order_id = self.env['sale.order'].search_count([
            ('user_id', '=', user.id),
            ('state', 'not in', ['draft', 'sent'])])
        quotations = self.env['sale.order'].search_count([
            ('user_id', '=', user.id), ('state', 'in', ['sent'])])
        purchase_order = self.env['purchase.order'].search_count([
            ('user_id', '=', user.id),
            ('state', 'not in', ['draft', 'sent', 'to approve'])])
        purchase_rfq = self.env['purchase.order'].search_count([
            ('user_id', '=', user.id),
            ('state', 'in', ['sent', 'to approve'])])
        return {
            'target': [order_id, quotations],
            'target_po': [purchase_order, purchase_rfq],
            'target_accounting': all_accounting
        }
