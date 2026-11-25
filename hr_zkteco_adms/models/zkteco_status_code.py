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
from odoo import api, fields, models


class ZktecoStatusCode(models.Model):
    """Maps a device's raw punch status to a check-in or a check-out.

    ZKTeco firmwares are not consistent: the same numeric code means
    "break out" on one terminal and "overtime in" on another, and a device
    with no in/out key sends 255 for everything. Keeping the table editable
    means a site can correct its own terminals without a patch.
    """
    _name = 'zkteco.status.code'
    _description = 'ZKTeco Punch Status Code'
    _order = 'sequence, code'
    _rec_name = 'display_label'

    sequence = fields.Integer(default=10)
    code = fields.Char(
        required=True, index=True,
        help='Raw value sent by the device in the status column of an '
             'ATTLOG line.',
    )
    name = fields.Char(required=True, help='Label shown on punch logs.')
    punch_type = fields.Selection([
        ('in', 'Check In'),
        ('out', 'Check Out'),
        ('auto', 'Device Decides'),
        ('ignore', 'Ignore'),
    ], required=True, default='auto', help=(
        "Check In / Check Out force the direction. Device Decides alternates: "
        "it closes the open attendance if there is one, otherwise it opens a "
        "new one. Ignore drops the punch without creating attendance."
    ))
    color = fields.Selection([
        ('success', 'Green'),
        ('info', 'Blue'),
        ('warning', 'Orange'),
        ('danger', 'Red'),
        ('muted', 'Grey'),
    ], default='info', help='Badge colour used for this code on punch logs.')
    company_id = fields.Many2one(
        'res.company', string='Company', index=True,
        help='Leave empty to apply the code to every company.',
    )
    active = fields.Boolean(default=True)
    display_label = fields.Char(compute='_compute_display_label')

    _code_company_uniq = models.Constraint(
        'unique (code, company_id)',
        'This status code is already configured for this company.',
    )

    @api.depends('code', 'name')
    def _compute_display_label(self):
        """Compute the display label using the status code and name."""
        for record in self:
            record.display_label = f"{record.code} - {record.name}"

    @api.model
    def _get_map(self, company):
        """Return {code: record} for a company, company-specific first.

        A row without a company is the fallback, so a site can override a
        single code for one company without redefining the whole table.
        """
        codes = self.sudo().search([
            ('company_id', 'in', [company.id, False] if company else [False]),
        ], order='company_id asc nulls first')
        mapping = {}
        for record in codes:
            # Company-specific rows come last and win.
            mapping[record.code] = record
        return mapping
