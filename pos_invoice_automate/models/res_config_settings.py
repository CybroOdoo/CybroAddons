# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class PosConfig(models.TransientModel):
    _inherit = 'res.config.settings'

    button_operation = fields.Selection(selection=[
        ('download', 'Download'),
        ('send', 'Send By Email'),
        ('download_send_mail', 'Download & Send By Email')
    ], string='Button Operation', related="pos_config_id.button_operation",
        help='The invoice button operation', readonly=False,
        config_parameter='pos_invoice_automate.button_operation')
    invoice_auto_check = fields.Boolean(
        related="pos_config_id.invoice_auto_check",
        help='Check to enable the invoice button',
        readonly=False, store=True,
        config_parameter='pos_invoice_automate.invoice_auto_check')

    @api.model
    def get_values(self):
        res = super(PosConfig, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            invoice_auto_check=get_param(
                'res.config.settings.invoice_auto_check'),
            button_operation=get_param('res.config.settings.button_operation'),
            external_email_server_default=get_param(
                'res.config.settings.external_email_server_default')
        )
        return res

    def set_values(self):
        res = super(PosConfig, self).get_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        res.update(
            invoice_auto_check=set_param(
                'res.config.settings.invoice_auto_check',
                self.invoice_auto_check),
            button_operation=set_param('res.config.settings.button_operation',
                                       self.button_operation),
            external_email_server_default=set_param(
                'res.config.settings.external_email_server_default',
                self.external_email_server_default)
        )
        return res
