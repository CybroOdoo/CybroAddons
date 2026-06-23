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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields


class NhsOdsTestConnectionWizard(models.TransientModel):
    """Transient wizard to test ODS API connection, latency, and endpoints."""
    _name = 'nhs.ods.test.connection.wizard'
    _description = 'NHS ODS Test Connection Wizard'

    probe_ods_code = fields.Char(
        string='Probe ODS Code',
        default='RW1',
        help="ODS code used for the test probe. Default: RW1 (Manchester University NHS FT).",
    )
    result_ok = fields.Boolean(
        string='Connection OK',
        readonly=True,
        help="Indicates if the API connection test was successful.",
    )
    result_latency_ms = fields.Integer(
        string='Latency (ms)',
        readonly=True,
        help="API response time in milliseconds.",
    )
    result_message = fields.Text(
        string='Result',
        readonly=True,
        help="Diagnostic message returned from the test connection.",
    )
    state = fields.Selection([
        ('init', 'Not tested'),
        ('success', 'Success'),
        ('warning', 'Slow'),
        ('error', 'Failed'),
    ], default='init', readonly=True,
        help="The resulting state of the connection test.",
    )

    def action_open(self):
        """Open the test connection wizard in a modal window."""
        return {
            'type': 'ir.actions.act_window',
            'name': ('Test ODS Connection'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_test(self):
        """Perform ping to the ODS API client and record connection statistics."""
        self.ensure_one()
        from ..services.ods_api_client import OdsApiClient
        client = OdsApiClient(self.env)
        ok, latency_ms, message = client.ping()
        if ok:
            if latency_ms > 2000:
                state = 'warning'
                message = f'OK but slow ({latency_ms} ms). Check network or rate limits.'
            else:
                state = 'success'
                message = f'Connected successfully in {latency_ms} ms.'
        else:
            state = 'error'
        self.write({
            'result_ok': ok,
            'result_latency_ms': latency_ms,
            'result_message': message,
            'state': state,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': ('Test ODS Connection'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

