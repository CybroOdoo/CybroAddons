# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ZktecoDeviceCommand(models.Model):
    _name = 'zkteco.device.command'
    _description = 'ZKTeco Device Command'
    _order = 'id desc'
    _rec_name = 'command'

    device_id = fields.Many2one(
        'zkteco.device', required=True, ondelete='cascade', index=True,
    )
    company_id = fields.Many2one(
        related='device_id.company_id', store=True, readonly=True,
    )
    command = fields.Char(
        required=True,
        help="ADMS command sent to the device on its next poll, e.g. "
             "'DATA QUERY ATTLOG', 'DATA QUERY USERINFO', 'CLEAR LOG', "
             "'REBOOT', 'INFO'.",
    )
    state = fields.Selection([
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], default='pending', required=True, index=True)
    sent_at = fields.Datetime(readonly=True)
    return_code = fields.Char(readonly=True)

    def action_retry(self):
        """Reset sent or failed records to pending state for retry."""
        self.filtered(lambda c: c.state in ('sent', 'error')).write({
            'state': 'pending', 'sent_at': False, 'return_code': False,
        })
