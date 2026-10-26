# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError



class PharmaValueSource(models.Model):
    """A registered device that may supply measured values.

    Nothing writes through a source yet. It exists so the origin marker on
    measured values has something to point at, without altering those tables
    a second time when a device is connected.

    Registering a source is part of the Device Capture add-on
    (pharma_device_capture): without it, sources can be viewed but not
    created.
    """
    _name = 'pharma.value.source'
    _description = 'Registered Measurement Source'
    _order = 'name'

    name = fields.Char(
        required=True,
        help='Specifies the name of the device, e.g. "Dispensary Balance 2".',
    )
    code = fields.Char(
        required=True,
        copy=False,
        help='Unique identifier the device is registered under.',
    )
    source_type = fields.Selection(
        selection=[
            ('balance', 'Balance'),
            ('instrument', 'Analytical Instrument'),
            ('sensor', 'Process Sensor'),
            ('other', 'Other'),
        ],
        string='Type',
        required=True,
        default='other',
        help='Specifies the kind of device.',
    )

    _code_uniq = models.Constraint(
        'unique(code)',
        'A measurement source code must be unique.',
    )

    @api.model
    def _pharma_device_capture_enabled(self):
        """Whether sources may be registered. The Device Capture add-on
        returns True."""
        return False

    @api.model_create_multi
    def create(self, vals_list):
        """Refuse to register a source without the Device Capture add-on."""
        if not self._pharma_device_capture_enabled():
            raise UserError(self.env._(
                'Registering a measurement source is part of the Device '
                'Capture add-on, which is not installed.'))
        return super().create(vals_list)

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        """Drop the create button without the Device Capture add-on."""
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ('list', 'form', 'kanban') and \
                not self._pharma_device_capture_enabled():
            arch.set('create', '0')
        return arch, view

    @api.model
    def get_empty_list_help(self, help_message):
        """Explain the lock on the empty list."""
        if self._pharma_device_capture_enabled():
            return super().get_empty_list_help(help_message)
        return super().get_empty_list_help(Markup(
            '<p class="o_view_nocontent_smiling_face">%s</p><p>%s</p>') % (
            self.env._('Device Capture is a premium add-on'),
            self.env._('Registering balances, instruments and sensors comes with the '
              'Device Capture add-on. Open Settings › Premium Features to '
              'learn more or get it on the Odoo Apps store.'),
        ))
