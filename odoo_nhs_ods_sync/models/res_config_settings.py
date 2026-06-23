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


class ResConfigSettings(models.TransientModel):
    """Extend transient config settings to support NHS ODS API configurations."""
    _inherit = 'res.config.settings'

    nhs_ods_contact_email = fields.Char(
        string='ODS Contact Email',
        config_parameter='nhs_ods_sync.contact_email',
        help="Sent as part of the User-Agent header so NHS Digital can identify the client.",
    )
    nhs_ods_timeout = fields.Integer(
        string='Request Timeout (seconds)',
        config_parameter='nhs_ods_sync.timeout',
        default=30,
        help="API request timeout in seconds.",
    )
    nhs_ods_rate_per_sec = fields.Float(
        string='Rate Limit (req/sec)',
        config_parameter='nhs_ods_sync.rate_per_sec',
        default=5.0,
        help="Maximum number of requests per second to avoid API rate limits.",
    )
    nhs_ods_default_mode = fields.Selection([
        ('live', 'Live'),
        ('dry_run', 'Dry Run'),
    ], string='Default Sync Mode',
        config_parameter='nhs_ods_sync.default_mode',
        default='live',
        help="Default operation mode for ODS synchronization.",
    )
    nhs_ods_auto_resolve_trivial = fields.Boolean(
        string='Auto-resolve trivial diffs (whitespace/casing)',
        config_parameter='nhs_ods_sync.auto_resolve_trivial',
        default=False,
        help="When True, trivial changes like casing and whitespace will be automatically resolved.",
    )
    nhs_ods_conflict_group_id = fields.Many2one(
        'res.groups',
        string='Conflict Notification Group',
        help="Users in this group receive an activity when a new conflict is detected.",
    )

    def action_test_ods_connection(self):
        """Return action to open the connection testing wizard."""
        self.ensure_one()
        wizard = self.env['nhs.ods.test.connection.wizard'].create({})
        return wizard.action_open()

