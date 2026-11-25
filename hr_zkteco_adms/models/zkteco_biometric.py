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
from odoo import _, api, fields, models


class ZktecoBiometricTemplate(models.Model):
    """Enrolment data read back from a terminal.

    Templates are vendor-encoded blobs, useless outside a ZKTeco device.
    They are stored so a replacement terminal can be seeded from Odoo
    instead of re-enrolling every employee at the door.
    """
    _name = 'zkteco.biometric.template'
    _description = 'ZKTeco Biometric Template'
    _order = 'device_user_id, template_type, finger_index'
    _rec_name = 'display_label'

    device_id = fields.Many2one(
        'zkteco.device', required=True, ondelete='cascade', index=True,
    )
    company_id = fields.Many2one(
        related='device_id.company_id', store=True, readonly=True,
    )
    device_user_id = fields.Many2one(
        'zkteco.device.user', string='Device User', required=True,
        ondelete='cascade', index=True,
    )
    employee_id = fields.Many2one(
        related='device_user_id.employee_id', store=True, readonly=True,
    )
    user_pin = fields.Char(related='device_user_id.user_pin', store=True, readonly=True)
    template_type = fields.Selection([
        ('finger', 'Fingerprint'),
        ('face', 'Face'),
        ('card', 'Card'),
    ], required=True, index=True)
    finger_index = fields.Integer(
        string='Finger', default=-1,
        help='0-9, left little finger to right little finger. -1 when the '
             'template is not a fingerprint.',
    )
    template_data = fields.Text(
        string='Template', help='Base64 of the vendor blob read from the device.',
    )
    card_number = fields.Char()
    size = fields.Integer(readonly=True)
    valid = fields.Boolean(default=True)
    display_label = fields.Char(compute='_compute_display_label')

    _template_uniq = models.Constraint(
        'unique (device_user_id, template_type, finger_index)',
        'This template already exists for that device user.',
    )

    FINGER_NAMES = [
        'Left Little', 'Left Ring', 'Left Middle', 'Left Index', 'Left Thumb',
        'Right Thumb', 'Right Index', 'Right Middle', 'Right Ring', 'Right Little',
    ]

    @api.depends('template_type', 'finger_index', 'device_user_id')
    def _compute_display_label(self):
        """Compute a descriptive label for the biometric template.
                For fingerprint templates, includes the corresponding finger name.
                For other template types, uses the configured selection label. The
                resulting label combines the device user and template type."""
        for record in self:
            if record.template_type == 'finger' and 0 <= record.finger_index < 10:
                kind = _('Fingerprint (%s)', record.FINGER_NAMES[record.finger_index])
            else:
                kind = dict(self._fields['template_type'].selection).get(
                    record.template_type, '')
            record.display_label = f"{record.device_user_id.display_label or ''} - {kind}".strip(' -')
