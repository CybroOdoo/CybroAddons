# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
################################################################################
from odoo import models


class SaleOrderLine(models.Model):
    """Extend Sale Order to add functionality."""
    _inherit = 'sale.order'

    def action_open_invoices(self):
        """
        This method opens a new window to link invoices and remove invoices
        for the current sale order.
        """
        partner_invoices = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('sale_order_count', '=', 0)
        ])
        return {
            "type": "ir.actions.act_window",
            "name": "Link Invoices and Remove Invoices",
            "view_mode": "form",
            "res_model": "link.invoice",
            "target": "new",
            "context": {
                'default_invoice_ids': [(6, 0, partner_invoices.ids)],
                'default_sale_order_id': self.id
            }
        }
