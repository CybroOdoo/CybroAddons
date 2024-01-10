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
import base64

from odoo import fields, models
from odoo.http import request


class PosOrder(models.Model):
    _inherit = 'pos.order'

    is_send = fields.Boolean(string='Is invoice send?',
                             help='Is the invoice is send or not')

    def send_mail_invoice(self):
        """Send invoice by email"""
        if not self.account_move:
            self.action_pos_order_invoice()
        template = self.env.ref('pos_invoice_automate.send_mail_template')
        email_values = {
            'email_to': self.partner_id.email,
            'email_from': self.env.user.partner_id.email,
        }
        attachment_invoice = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.account_move.id)])
        if not attachment_invoice:
            report = self.env['ir.actions.report']._render_qweb_pdf(
                "account.account_invoices", self.account_move.ids[0])

            values = {
                'name': "Invoice" + self.name,
                'type': 'binary',
                'datas': base64.b64encode(report[0]),
                'store_fname': base64.b64encode(report[0]),
                'mimetype': 'application/pdf',
            }
            attachment_invoice = self.env['ir.attachment'].sudo().create(
                values)
        template.attachment_ids = [(6, 0, [attachment_invoice.id])]
        self.env['mail.template'].browse(template.id).send_mail(
            self.id, email_values=email_values, force_send=True)
        self.is_send = True
        attachment_url = f"""{request.httprequest.host_url[:-1]}/web/content/{attachment_invoice.id}"""

        return {
            'type': 'ir.actions.act_url',
            'url': attachment_url + '?download=true',
        }

    def download_invoice(self):
        if not self.account_move:
            self.action_pos_order_invoice()
        template = self.env.ref('pos_invoice_automate.send_mail_template')
        attachment_invoice = self.env['ir.attachment'].search([
            ('res_model', '=', 'account.move'),
            ('res_id', '=', self.account_move.id)])
        if not attachment_invoice:
            report = self.env['ir.actions.report']._render_qweb_pdf(
                "account.account_invoices", self.account_move.ids[0])

            values = {
                'name': "Invoice" + self.name,
                'type': 'binary',
                'datas': base64.b64encode(report[0]),
                'store_fname': base64.b64encode(report[0]),
                'mimetype': 'application/pdf',
            }
            attachment_invoice = self.env['ir.attachment'].sudo().create(
                values)
        template.attachment_ids = [(6, 0, [attachment_invoice.id])]
        attachment_url = f"""{request.httprequest.host_url[:-1]}/web/content/{attachment_invoice.id}"""

        return {
            'type': 'ir.actions.act_url',
            'url': attachment_url + '?download=true',
        }
