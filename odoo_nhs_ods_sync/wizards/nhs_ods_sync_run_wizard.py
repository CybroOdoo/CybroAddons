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
from odoo import models, fields, api
from odoo.exceptions import UserError


class NhsOdsSyncRunWizard(models.TransientModel):
    """Transient wizard to configure and trigger an ODS sync run manually."""
    _name = 'nhs.ods.sync.run.wizard'
    _description = 'NHS ODS Sync — Run Wizard'

    mode = fields.Selection([
        ('live', 'Live (apply changes)'),
        ('dry_run', 'Dry Run (preview only)'),
    ], string='Mode', required=True, default='live',
        help="Select 'Live' to write updates to trusts, or 'Dry Run' to only preview differences.",
    )
    scope = fields.Selection([
        ('all_roles', 'All Roles'),
        ('specific_role', 'Specific Role'),
        ('specific_org', 'Specific Organisation'),
    ], string='Scope', required=True, default='all_roles',
        help="Define scope: synchronize all roles, a specific mapped role, or a single targeted organisation.",
    )
    role_mapping_id = fields.Many2one(
        'nhs.ods.role.mapping',
        string='Role Mapping',
        help="Role mapping record to synchronize.",
    )
    ods_code = fields.Char(
        string='ODS Code',
        help="Enter the exact ODS code of the organisation to target.",
    )
    delta_since = fields.Date(
        string='Delta Since',
        help="When set, only fetch orgs changed on or after this date.",
    )

    @api.model
    def default_get(self, fields_list):
        """Load default sync mode configuration parameter from the settings."""
        res = super().default_get(fields_list)
        cp = self.env['ir.config_parameter'].sudo()
        default_mode = cp.get_param('nhs_ods_sync.default_mode', 'live')
        if 'mode' in fields_list:
            res['mode'] = default_mode
        return res

    def action_confirm(self):
        """Validate selections, instantiate, and execute the NHS ODS sync run."""
        self.ensure_one()
        if self.scope == 'specific_role' and not self.role_mapping_id:
            raise UserError(("Please select a role mapping for a role-specific sync."))
        if self.scope == 'specific_org' and not self.ods_code:
            raise UserError(("Please provide an ODS code for a targeted sync."))

        run_type = 'dry_run' if self.mode == 'dry_run' else (
            'targeted' if self.scope == 'specific_org' else 'incremental' if self.delta_since else 'full'
        )

        run_vals = {
            'run_type': run_type,
            'triggered_by': 'manual',
            'user_id': self.env.user.id,
        }
        if self.delta_since:
            run_vals['delta_since'] = self.delta_since
        if self.scope == 'specific_org' and self.ods_code:
            run_vals['targeted_ods_code'] = self.ods_code.strip().upper()

        run = self.env['nhs.ods.sync.run'].create(run_vals)
        run.action_run()

        return {
            'type': 'ir.actions.act_window',
            'name': ('Sync Run'),
            'res_model': 'nhs.ods.sync.run',
            'res_id': run.id,
            'view_mode': 'form',
            'target': 'current',
        }

