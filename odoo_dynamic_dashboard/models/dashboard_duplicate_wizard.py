# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import api, fields, models


class DashboardDuplicateWizard(models.TransientModel):
    """Wizard to duplicate an existing dashboard."""
    _name = 'dashboard.duplicate.wizard'
    _description = 'Duplicate Dashboard Wizard'

    dashboard_id = fields.Many2one(
        'dashboard.menu',
        string='Dashboard',
        required=True,
        help='Select the dashboard to duplicate.'
    )
    new_name = fields.Char(
        string='New Dashboard Name',
        required=True,
        help='Name for the new dashboard.'
    )
    parent_id = fields.Many2one(
        'ir.ui.menu',
        string='Parent Menu',
        required=True,
        domain=[('action', '=', False)],
        help='Menu under which the new dashboard will be placed.'
    )

    @api.model
    def default_get(self, fields_list):
        """Populate default values from the active dashboard context."""
        res = super(DashboardDuplicateWizard, self).default_get(fields_list)
        if self._context.get('active_id'):
            dashboard = self.env['dashboard.menu'].browse(self._context.get('active_id'))
            if dashboard.exists():
                res['dashboard_id'] = dashboard.id
                res['new_name'] = '{0} (Copy)'.format(dashboard.name)
                res['parent_id'] = dashboard.parent_id.id
        return res

    def action_confirm(self):
        """Confirm the duplication of the dashboard."""
        self.ensure_one()
        return self.dashboard_id.action_duplicate_dashboard(self.new_name, self.parent_id.id)
