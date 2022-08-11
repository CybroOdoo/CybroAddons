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
from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    button_operation = fields.Selection(selection=[
        ('download', 'Download'),
        ('send', 'Send By Email'),
        ('download_send_mail', 'Download & Send By Email')
    ], string='Button Operation', help='The invoice button operation')
    interval = fields.Integer(help='Time interval for the cron scheduler')
    period = fields.Selection(selection=[
        ('minutes', 'Minute'),
        ('hours', 'Hour'),
        ('days', 'Day'),
        ('weeks', 'Week'),
        ('months', 'Months')
    ], string='Period', help='Period for the cron scheduler')
    is_started = fields.Boolean(default=False, help='Is the cron is started')
    is_stopped = fields.Boolean(default=True, help='Is the cron is stopped')
    invoice_auto_check = fields.Boolean(
        help='Check to enable the invoice button')

    def start_cron(self):
        """Start the cron scheduler"""
        self.is_started = True
        self.is_stopped = False
        send_mail_ir_cron = self.env.ref(
            'pos_invoice_automate.ir_cron_send_invoice')
        send_mail_ir_cron.write({
            'interval_number': self.interval,
            'interval_type': self.period,
            'active': True,
            'numbercall': 1,
            'code': 'model._send_mail(%s)' % (self.id)
        })

    def stop_cron(self):
        """Stop the cron scheduler"""
        self.is_stopped = True
        self.is_started = False
        send_mail_ir_cron = self.env.ref(
            'pos_invoice_automate.ir_cron_send_invoice')
        send_mail_ir_cron.write({
            'active': False,
        })

    def _send_mail(self, config):
        """Send invoice by Email"""
        point_of_sale = self.env['pos.config'].browse(config)
        for order in point_of_sale.mapped(
                'session_ids').mapped('order_ids').filtered(
                lambda x: x.state == 'invoiced' and not x.is_send):
            order.send_mail_invoice()
