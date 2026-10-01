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

from odoo import fields, models


class AddToDashboardWizard(models.TransientModel):
    """Wizard to add view to dashboard"""
    _name = 'add.to.dashboard.wizard'
    _description = 'Wizard To Add View To Dashboard'

    dashboard_menu_id = fields.Many2one(
        'dashboard.menu',
        string='Select Dashboard',
        required=True,
        help='Select the dashboard where the view will be added.'
    )
    card_name = fields.Char(
        string='Card Title',
        required=True,
        help='Title for the new dashboard card.'
    )
    res_model = fields.Char(string='Model', help='Technical model name.')
    view_type = fields.Char(string='View Type', help='Type of the view to be added.')
    domain = fields.Char(string='Domain', help='Filter domain of the view.')

    def action_add_to_dashboard(self):
        """Add the selected view as a card to the dashboard."""
        self.ensure_one()
        model = self.env['ir.model'].search([('model', '=', self.res_model)], limit=1)

        is_activity_source = self.view_type == 'activity'
        card_main_type = 'activity' if is_activity_source else 'views'

        vals = {
            'name': self.card_name,
            'description': "Added from {0} {1} view".format(self.res_model, self.view_type),
            'model_id': model.id,
            'dashboard_menu_id': self.dashboard_menu_id.id,
            'domain': self.domain,
            'type': card_main_type,
            'gs_w': 3,
            'gs_h': 2,
        }

        # 2. Assign subtype fields correctly to avoid ValueError
        if is_activity_source:
            vals['activity_type'] = 'timeline'
            vals['view_type'] = 'kanban'
        else:
            # For standard views (list, kanban, pivot, etc.)
            vals['view_type'] = self.view_type

        self.env['dashboard.card'].create(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Added to Dashboard successfully',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
