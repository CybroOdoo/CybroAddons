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
from contextlib import contextmanager
from contextvars import ContextVar

from odoo import api, fields, models

# The device source a trusted server-side capture is writing for. A context
# variable rather than an Odoo context key, because the Odoo context arrives
# with every RPC call and could be set by any client; this can only be set by
# Python code running inside the server.
_DEVICE_SOURCE = ContextVar('pharma_device_source', default=None)


@contextmanager
def device_capture(source):
    """Mark measured values written inside this block as device-captured.

    To be entered only by the code that has authenticated the device, e.g.::

        with device_capture(source):
            result_line.write({'actual_value': reading})
    """
    token = _DEVICE_SOURCE.set(source.id)
    try:
        yield
    finally:
        _DEVICE_SOURCE.reset(token)


class PharmaMeasuredValueMixin(models.AbstractModel):
    """Records how a measured value arrived: typed by a person or from a device.

    Models list the fields that hold their measured value in
    ``_measured_fields``. The origin is stamped on create and whenever one of
    those fields is written. Anything not inside ``device_capture`` is manual:
    a missed code path must never claim transcribed data was machine-captured.
    """
    _name = 'pharma.measured.value.mixin'
    _description = 'Measured Value Origin'

    _measured_fields = ()

    value_origin = fields.Selection(
        selection=[
            ('manual', 'Entered by a Person'),
            ('device', 'Captured from a Device'),
        ],
        required=True,
        readonly=True,
        copy=False,
        default='manual',
        help='How the measured value arrived. Set by the system on save; it '
             'cannot be entered.',
    )
    value_source_id = fields.Many2one(
        comodel_name='pharma.value.source',
        readonly=True,
        copy=False,
        ondelete='restrict',
        index='btree_not_null',
        help='Registered device that captured the value, when it was not '
             'entered by a person.',
    )

    def _pharma_value_origin_vals(self):
        """Origin of a value being written now; manual unless a device capture."""
        source_id = _DEVICE_SOURCE.get()
        return {
            'value_origin': 'device' if source_id else 'manual',
            'value_source_id': source_id or False,
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Stamp the origin of every new record, ignoring any value supplied."""
        origin = self._pharma_value_origin_vals()
        for vals in vals_list:
            vals.update(origin)
        return super().create(vals_list)

    def write(self, vals):
        """Restamp the origin when the measured value changes; never accept one."""
        vals.pop('value_origin', None)
        vals.pop('value_source_id', None)
        if any(name in vals for name in self._measured_fields):
            vals.update(self._pharma_value_origin_vals())
        return super().write(vals)
