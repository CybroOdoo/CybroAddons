# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo import models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherits 'account.move' and added action for 'Custom Invoice' button """
    _inherit = 'account.move'

    def action_print_custom_invoice(self):
        """Prints custom invoice on clicking 'Print Custom Invoice' option"""
        invoice_design = self.env['ir.config_parameter'].sudo().get_param(
            'invoice_design.invoice_design')
        data = {
            'key': self.env['ir.ui.view'].browse(
                self.env['invoice.design'].browse(
                    int(invoice_design)).view_id.id).key,
            'id': self.id,
        }
        if self.env['ir.config_parameter'].sudo().get_param(
                'invoice_design.is_custom_invoice'):
            return (self.env.ref('invoice_design.action_invoice_design').
                    report_action(None, data=data))
        else:
            raise UserError(_('You can print custom invoice after choosing a '
                              'custom design from configuration settings'))
