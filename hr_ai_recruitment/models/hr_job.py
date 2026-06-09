# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
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

class HrJob(models.Model):
    """
    Inherit of hr.job to provide AI-based shortlisting functionality.
    Adds a flag to enable AI shortlisting, tracks shortlisted applicants,
    and opens a shortlist wizard form.
    """
    _inherit = 'hr.job'

    ai_shortlist_enabled = fields.Boolean(
        compute='_compute_ai_shortlist_enabled',
        string="AI Shortlist Enabled",
        help="Indicates whether AI-powered shortlisting is enabled (via configuration parameter)."
    )
    shortlisted_applicant_ids = fields.Many2many(
        'hr.applicant',
        string="Shortlisted Applicants",
        domain="([('job_id', '=', id)])",
        help="Applicants selected by the AI shortlisting process for this job."
    )

    def action_shortlist(self):
        """
        Open the AI shortlist wizard in a form view.
        Uses a pop-up form to trigger the AI shortlisting process
        for the current job.
        """
        shortlist_form_id = self.env.ref(
            'hr_ai_recruitment.hr_ai_shortlist_view_form'
        ).id
        return {
            'name': "Shortlist",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.ai.shortlist',
            'views': [(shortlist_form_id, 'form')],
            'view_id': shortlist_form_id,
            'target': 'new',
            'context': {'default_job_id': self.id},
        }

    def _compute_ai_shortlist_enabled(self):
        """
        Compute whether AI shortlisting is enabled.
        Checks system parameter 'hr_ai_recruitment.is_ai_shortlist'
        and sets the boolean flag accordingly.
        """
        param = self.env['ir.config_parameter'].sudo().get_param(
            'hr_ai_recruitment.is_ai_shortlist'
        )
        enabled = (param == 'True')
        for rec in self:
            rec.ai_shortlist_enabled = enabled
