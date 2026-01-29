# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    state = fields.Selection(selection_add=
                             [('to_approve', 'To Approve')], ondelete={'to_approve': 'cascade'})

    def button_approve(self):
        self.action_confirm()

    def action_confirm(self):
        if not self.user_has_groups('sales_team.group_sale_manager'):
            if self.company_id.so_double_validation:
                if self.env['ir.config_parameter'].sudo().get_param('sales_order_double_approval.so_approval'):
                    if self.amount_total > float(
                            self.env['ir.config_parameter'].sudo().get_param('sales_order_double_approval.so_min_amount')):
                        self.state = 'to_approve'
                        return
        return super(SaleOrder, self).action_confirm()

    def action_cancel(self):
        self.state = 'cancel'
