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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    invoice_auto_check = fields.Boolean()
    button_operation = fields.Selection(selection=[
        ('download', 'Download'),
        ('send', 'Send By Email'),
        ('download_send_mail', 'Download & Send By Email')
    ])
    interval = fields.Integer(help='Time interval for the cron scheduler',
                              string="Time Interval",
                              required=True)
    period = fields.Selection(selection=[
        ('minutes', 'Minute'),
        ('hours', 'Hour'),
        ('days', 'Day'),
        ('weeks', 'Week'),
        ('months', 'Months')
    ], string='Period', help='Period for the cron scheduler', required=True)
    is_started = fields.Boolean(default=False, help='Is the cron is started')
    is_stopped = fields.Boolean(default=True, help='Is the cron is stopped')

    def start_cron(self):
        """Start the cron scheduler"""
        if self.interval >= 0:
            self.is_started = True
            self.is_stopped = False
            cron_values = {
                'name': 'POS (%s): Send Invoice By Email' % (self.name),
                'interval_number': self.interval,
                'interval_type': self.period,
                'numbercall': 1,
                'active': True,
                'model_id': self.env['ir.model']._get('pos.config').id,
                'code': 'model._send_mail(%s)' % (self.id),
                'config_id': self.id
            }
            self.env['ir.cron'].create(cron_values)
        else:
            raise ValidationError(_('Negative number should not be allowed.'))

    def stop_cron(self):
        """Stop the cron scheduler"""
        ir_crone = self.env['ir.cron'].search(
            [('config_id', '=', self.id), ('active', '=', True)])
        if ir_crone:
            ir_crone.write({'active': False})
            self.is_stopped = True
            self.is_started = False

    def _send_mail(self, config):
        """Send invoice by Email"""
        point_of_sale = self.env['pos.config'].browse(config)
        for order in point_of_sale.session_ids.order_ids.filtered(
                lambda x: x.state == 'invoiced' and not x.is_send):
            order.send_mail_invoice()
