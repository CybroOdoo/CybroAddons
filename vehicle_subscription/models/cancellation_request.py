# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed (<https://www.cybrosys.com>)
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


class CancellationRequest(models.Model):
    """Created new model to add new fields and function"""
    _name = "cancellation.request"
    _description = "Cancellation Request"
    _inherit = "mail.thread"
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('fleet.vehicle',
                                 string="Vehicle", help="Choose vehicle "
                                                        "inorder to cancel "
                                                        "subscription")
    date = fields.Date(string="Cancellation Date", default=fields.Date.today(),
                       help="Date for cancellation of vehicle")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="Choose Customer for the cancellation "
                                       "of vehicle")
    reason = fields.Char(string="Cancellation Reason", help="Describe the "
                                                            "reason for "
                                                            "cancellation")
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('to_approve', 'To Approve'),
                                        ('approved', 'Approved')],
                             string='State', default='draft',
                             help="States of cancellation subscription")

    def action_request(self):
        """Change state to to_approve"""
        self.write({'state': 'to_approve'})

    def action_approve(self):
        """Handle cancellation approval by manager.
        This method handles the approval process for a cancellation
        request in a vehicle subscription system.
        It updates the cancellation state, generates invoices or refunds
        based on the payment status, and sends notifications to the customer."""
        self.write({'state': 'approved'})
        subscription = self.env['fleet.subscription'].search(
            [('vehicle_id', '=', self.vehicle_id.id),
             ('customer_id', '=', self.customer_id.id)])
        invoice = subscription.sale_id.invoice_ids
        multy_invoice = subscription.invoice_ids.ids
        product_template_id = self.env.ref(
            'vehicle_subscription.product_template_vehicle_subscription_form').id
        product_id = self.env['product.product'].search(
            [('product_tmpl_id', '=', product_template_id)])
        per_day_price = subscription.sale_id.amount_untaxed / subscription.duration
        invoice_duration = (self.date - subscription.start_date).days
        email_template = self.env.ref(
            'vehicle_subscription.cancellation_request_mail')
        template_approved = self.env.ref(
            'vehicle_subscription.cancellation_approved')
        refund_approved = self.env.ref(
            'vehicle_subscription.cancellation_request_refund_mail')
        uptodate_price = round(per_day_price * invoice_duration, 2)
        paid_amount = self.env['account.move'].search(
            [('id', 'in', subscription.invoice_ids.ids),
             ('payment_state', 'in', ['paid', 'partial'])]) \
            .mapped('amount_untaxed_signed')
        if paid_amount:
            if sum(paid_amount) == uptodate_price:
                subscription.state = 'cancel'
                email_values = {
                    'email_to': self.customer_id.email,
                    'email_from': self.env.user.email,
                }
                template_approved.send_mail(self.id, email_values=email_values,
                                            force_send=True)
            elif sum(paid_amount) < uptodate_price:
                if len(invoice) == 1 or len(multy_invoice) == 1:
                    invoice.button_cancel()
                    generate_invoice = self.env['account.move'].sudo().create({
                        'move_type': 'out_invoice',
                        'partner_id': self.customer_id.id,
                        'invoice_date': self.date,
                        'invoice_line_ids': [(0, 0, {
                            'product_id': product_id.id,
                            'name': self.vehicle_id.name,
                            'price_unit':
                                (per_day_price * invoice_duration) - sum(
                                    paid_amount),
                        })]
                    })
                    generate_invoice.action_post()
                    data_record = base64.b64encode(
                        self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                            "account.account_invoices",
                            generate_invoice.ids)[0])
                    ir_values = {
                        'name': 'Invoice',
                        'type': 'binary',
                        'datas': data_record,
                        'store_fname': 'invoice.pdf',
                        'mimetype': 'application/pdf',
                        'res_model': 'account.move',
                        'res_id': generate_invoice.id,
                    }
                    invoice_report_attachment_id = self.env[
                        'ir.attachment'].sudo().create(
                        ir_values)
                    email_values = {
                        'email_to': self.customer_id.email,
                        'email_from': self.env.user.email,
                        'attachment_ids': [
                            (4, invoice_report_attachment_id.id, None)]
                    }
                    email_template.send_mail(self.id, email_values=email_values,
                                             force_send=True)
                    email_template.attachment_ids = [(5, 0, 0)]
                    subscription.invoice_ids = [(4, generate_invoice.id)]
                    subscription.sale_id.write({
                        'invoice_ids': [(4, generate_invoice.id)]
                    })
                else:
                    for invoice_id in multy_invoice:
                        invoice = self.env['account.move'].browse(invoice_id)
                        invoice.button_cancel()
                    generate_invoice = self.env['account.move'].sudo().create({
                        'move_type': 'out_invoice',
                        'partner_id': self.customer_id.id,
                        'invoice_date': self.date,
                        'invoice_line_ids': [(0, 0, {
                            'product_id': product_id.id,
                            'name': self.vehicle_id.name,
                            'price_unit':
                                (per_day_price * invoice_duration) - sum(
                                    paid_amount),
                        })]
                    })
                    generate_invoice.action_post()
                    data_record = base64.b64encode(
                        self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                            "account.account_invoices",
                            generate_invoice.ids)[0])
                    ir_values = {
                        'name': 'Invoice',
                        'type': 'binary',
                        'datas': data_record,
                        'store_fname': 'invoice.pdf',
                        'mimetype': 'application/pdf',
                        'res_model': 'account.move',
                        'res_id': generate_invoice.id,
                    }
                    invoice_report_attachment_id = self.env[
                        'ir.attachment'].sudo().create(
                        ir_values)
                    email_values = {
                        'email_to': self.customer_id.email,
                        'email_from': self.env.user.email,
                        'attachment_ids': [
                            (4, invoice_report_attachment_id.id, None)]
                    }
                    email_template.send_mail(self.id, email_values=email_values,
                                             force_send=True)
                    email_template.attachment_ids = [(5, 0, 0)]
                    subscription.invoice_ids = [(4, generate_invoice.id)]
                    subscription.sale_id.write({
                        'invoice_ids': [(4, generate_invoice.id)]
                    })
            else:
                generate_refund = self.env['account.move'].sudo().create({
                    'move_type': 'out_refund',
                    'invoice_date': fields.Date.today(),
                    'partner_id': self.customer_id.id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product_id.id,
                        'name': self.vehicle_id.name,
                        'price_unit': (sum(paid_amount) - uptodate_price)
                    })]
                })
                generate_refund.action_post()
                subscription.refund_id = generate_refund
                data_record = base64.b64encode(
                    self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                        "account.account_invoices",
                        generate_refund.ids)[0])
                ir_values = {
                    'name': 'Invoice',
                    'type': 'binary',
                    'datas': data_record,
                    'store_fname': 'invoice.pdf',
                    'mimetype': 'application/pdf',
                    'res_model': 'account.move',
                    'res_id': generate_refund.id,
                }
                invoice_report_attachment_id = self.env[
                    'ir.attachment'].sudo().create(
                    ir_values)
                email_values = {
                    'email_to': self.customer_id.email,
                    'email_from': self.env.user.email,
                    'attachment_ids': [
                        (4, invoice_report_attachment_id.id, None)]
                }
                refund_approved.send_mail(self.id, email_values=email_values,
                                          force_send=True)
                refund_approved.attachment_ids = [(5, 0, 0)]
        else:
            invoice.button_cancel()
            generate_invoice = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': self.customer_id.id,
                'invoice_date': self.date,
                'invoice_line_ids': [(0, 0, {
                    'product_id': product_id.id,
                    'name': self.vehicle_id.name,
                    'price_unit': per_day_price * invoice_duration,
                })]
            })
            generate_invoice.action_post()
            data_record = base64.b64encode(
                self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                    "account.account_invoices",
                    generate_invoice.ids)[0])
            ir_values = {
                'name': 'Invoice',
                'type': 'binary',
                'datas': data_record,
                'store_fname': 'invoice.pdf',
                'mimetype': 'application/pdf',
                'res_model': 'account.move',
                'res_id': generate_invoice.id,
            }
            invoice_report_attachment_id = self.env[
                'ir.attachment'].sudo().create(
                ir_values)
            email_values = {
                'email_to': self.customer_id.email,
                'email_from': self.env.user.email,
                'attachment_ids': [(4, invoice_report_attachment_id.id, None)]
            }
            email_template.send_mail(self.id, email_values=email_values,
                                     force_send=True)
            email_template.attachment_ids = [(5, 0, 0)]
            subscription.invoice_ids = [(4, generate_invoice.id)]
            subscription.sale_id.write({
                'invoice_ids': [(4, generate_invoice.id)]
            })
