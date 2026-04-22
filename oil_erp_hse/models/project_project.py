# -*- coding: utf-8 -*-
#############################################################################
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
from odoo import fields, models
from odoo.tools.translate import _


class ProjectProject(models.Model):
    """
    Extends 'project.project' to provide integrated visibility into HSE metrics 
    (incidents, inspections, permits, risks) for oil and gas projects.
    """
    _inherit = 'project.project'

    hse_incident_count = fields.Integer(
        string='Incidents',
        compute='_compute_hse_counts',
        help="Enter the incidents.")
    hse_inspection_count = fields.Integer(
        string='Inspections',
        compute='_compute_hse_counts',
        help="Enter the inspections.")
    hse_permit_count = fields.Integer(
        string='Work Permits',
        compute='_compute_hse_counts',
        help="Enter the work Permits.")
    hse_risk_count = fields.Integer(
        string='Risk Assessments',
        compute='_compute_hse_counts',
        help="Enter the risk Assessments.")

    def _hse_project_domain(self):
        """
        Returns a domain that covers both direct project-linked and indirect 
        task-linked HSE records for this project.
        """
        self.ensure_one()
        return ['|', ('project_id', '=', self.id),
                ('task_id.project_id', '=', self.id)]

    def _compute_hse_counts(self):
        """
        Computes the counts for all HSE-related components for the project's dashboard.
        """
        incident_model = self.env['oil.hse.incident']
        inspection_model = self.env['oil.hse.inspection']
        permit_model = self.env['oil.hse.permit']
        risk_model = self.env['oil.hse.risk']
        for rec in self:
            project_domain = rec._hse_project_domain()
            rec.hse_incident_count = incident_model.search_count(project_domain)
            rec.hse_inspection_count = inspection_model.search_count(project_domain)
            rec.hse_permit_count = permit_model.search_count(project_domain)
            rec.hse_risk_count = risk_model.search_count(project_domain)

    def _get_hse_action(self, xmlid, domain):
        """Build an HSE action with the project defaults applied."""
        action = self.env.ref(xmlid).read()[0]
        action['domain'] = domain
        action['context'] = dict(self.env.context, default_project_id=self.id)
        return action

    def action_view_hse_incidents(self):
        """Open HSE incidents related to this project."""
        self.ensure_one()
        return self._get_hse_action(
            'oil_erp_hse.action_oil_hse_incident',
            self._hse_project_domain(),
        )

    def action_view_hse_inspections(self):
        """Open HSE inspections related to this project."""
        self.ensure_one()
        return self._get_hse_action(
            'oil_erp_hse.action_oil_hse_inspection',
            self._hse_project_domain(),
        )

    def action_view_hse_permits(self):
        """Open work permits related to this project."""
        self.ensure_one()
        return self._get_hse_action(
            'oil_erp_hse.action_oil_hse_permit',
            self._hse_project_domain(),
        )

    def action_view_hse_risks(self):
        """Open HSE risks related to this project."""
        self.ensure_one()
        return self._get_hse_action(
            'oil_erp_hse.action_oil_hse_risk',
            self._hse_project_domain(),
        )

    def action_report_incident(self) -> dict:
        """Open a blank oil.hse.incident form pre-linked to this project."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Report Incident'),
            'res_model': 'oil.hse.incident',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                # No task — incident is at project/field level.
                # The user can pick a specific task inside the form.
                'default_project_id': self.id,
                'default_task_id': False,
                # Pass company so multi-company default_get works correctly.
                'default_company_id': self.company_id.id,
            },
        }
