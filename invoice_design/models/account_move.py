# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Adds the 'Print Custom Invoice' action to 'account.move'."""
    _inherit = 'account.move'

    def _get_custom_invoice_report_data(self):
        """Return the data passed to the custom invoice report.

        Raise a UserError if custom invoices are disabled or no design
        is selected in the configuration settings."""
        params = self.env['ir.config_parameter'].sudo()
        is_enabled = params.get_str('invoice_design.is_custom_invoice')
        design_id = params.get_str('invoice_design.invoice_design')
        design = self.env['invoice.design']
        if design_id and design_id.isdigit():
            design = self.env['invoice.design'].sudo().browse(
                int(design_id)).exists()
        if not is_enabled or is_enabled == 'False' or not design.view_id:
            raise UserError(self.env._(
                'You can print a custom invoice after choosing a custom '
                'design in the configuration settings.'))
        return {
            'key': design.view_id.key,
            'move_ids': self.ids,
        }

    def action_print_custom_invoice(self):
        """Print the selected invoices using the design chosen in the
        configuration settings."""
        data = self._get_custom_invoice_report_data()
        return self.env.ref(
            'invoice_design.action_invoice_design').report_action(
                None, data=data)
