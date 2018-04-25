# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, fields, api, SUPERUSER_ID


class HrAppraisalForm(models.Model):
    _name = 'hr.appraisal'
    _inherit = 'mail.thread'
    _rec_name = 'emp_id'
    _description = 'Appraisal'

    @api.model
    def _read_group_stage_ids(self, categories, domain, order):
        """ Read all the stages and display it in the kanban view, even if it is empty."""
        category_ids = categories._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return categories.browse(category_ids)

    def _default_stage_id(self):
        """Setting default stage"""
        rec = self.env['hr.appraisal.stages'].search([], limit=1, order='sequence ASC')
        return rec.id if rec else None

    emp_id = fields.Many2one('hr.employee', string="Employee", required=True)
    appraisal_deadline = fields.Date(string="Appraisal Deadline", required=True)
    final_interview = fields.Date(string="Final Interview", help="After sending survey link,you can"
                                                                 " schedule final interview date")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    hr_manager = fields.Boolean(string="Manager", default=False)
    hr_emp = fields.Boolean(string="Employee", default=False)
    hr_colloborator = fields.Boolean(string="Collaborators", default=False)
    hr_colleague = fields.Boolean(string="Colleague", default=False)
    hr_manager_id = fields.Many2many('hr.employee', 'manager_appraisal_rel', string="Select Appraisal Reviewer")
    hr_colleague_id = fields.Many2many('hr.employee', 'colleagues_appraisal_rel',
                                       string="Select Appraisal Reviewer")
    hr_colloborator_id = fields.Many2many('hr.employee', 'colloborators_appraisal_rel',
                                          string="Select Appraisal Reviewer")
    manager_survey_id = fields.Many2one('survey.survey', string="Select Opinion Form")
    emp_survey_id = fields.Many2one('survey.survey', string="Select Appraisal Form")
    colloborator_survey_id = fields.Many2one('survey.survey', string="Select Opinion Form")
    colleague_survey_id = fields.Many2one('survey.survey', string="Select Opinion Form")
    response_id = fields.Many2one('survey.user_input', "Response", ondelete="set null", oldname="response")
    final_evaluation = fields.Text(string="Final Evaluation")
    app_period_from = fields.Date("From", required=True, readonly=True, default=fields.Datetime.now())
    tot_comp_survey = fields.Integer(string="Count Answers", compute="_compute_completed_survey")
    tot_sent_survey = fields.Integer(string="Count Sent Questions")
    created_by = fields.Many2one('res.users', string="Created By", default=lambda self: self.env.uid)
    state = fields.Many2one('hr.appraisal.stages', string='Stage', track_visibility='onchange', index=True,
                            default=lambda self: self._default_stage_id(),
                            group_expand='_read_group_stage_ids')
    # for coloring the kanban box
    color = fields.Integer(string="Color Index")
    check_sent = fields.Boolean(string="Check Sent Mail", default=False, copy=False)
    check_draft = fields.Boolean(string="Check Draft", default=True, copy=False)
    check_cancel = fields.Boolean(string="Check Cancel", default=False, copy=False)
    check_done = fields.Boolean(string="Check Done", default=False, copy=False)

    @api.multi
    def action_done(self):
        rec = self.env['hr.appraisal.stages'].search([('sequence', '=', 3)])
        self.state = rec.id
        self.check_done = True
        self.check_draft = False

    @api.multi
    def action_set_draft(self):
        rec = self.env['hr.appraisal.stages'].search([('sequence', '=', 1)])
        self.state = rec.id
        self.check_draft = True
        self.check_sent = False

    @api.multi
    def action_cancel(self):
        rec = self.env['hr.appraisal.stages'].search([('sequence', '=', 4)])
        self.state = rec.id
        self.check_cancel = True
        self.check_draft = False

    @api.multi
    def fetch_appraisal_reviewer(self):
        appraisal_reviewers = []
        if self.hr_manager and self.hr_manager_id and self.manager_survey_id:
            appraisal_reviewers.append((self.hr_manager_id, self.manager_survey_id))
        if self.hr_emp and self.emp_survey_id:
            appraisal_reviewers.append((self.emp_id, self.emp_survey_id))
        if self.hr_colloborator and self.hr_colloborator_id and self.colloborator_survey_id:
            appraisal_reviewers.append((self.hr_colloborator_id, self.colloborator_survey_id))
        if self.hr_colleague and self.hr_colleague_id and self.colleague_survey_id:
            appraisal_reviewers.append((self.hr_colleague_id, self.colleague_survey_id))
        return appraisal_reviewers

    @api.multi
    def action_start_appraisal(self):
        """ This function will start the appraisal by sending emails to the corresponding employees
            specified in the appraisal"""
        send_count = 0
        appraisal_reviewers_list = self.fetch_appraisal_reviewer()
        for appraisal_reviewers, survey_id in appraisal_reviewers_list:
            for reviewers in appraisal_reviewers:
                url = survey_id.public_url
                response = self.env['survey.user_input'].create(
                    {'survey_id': survey_id.id, 'partner_id': reviewers.user_id.partner_id.id,
                     'appraisal_id': self.ids[0],  'deadline': self.appraisal_deadline, 'email': reviewers.user_id.email})
                token = response.token
                if token:
                    url = url + '/' + token
                    mail_content = "Dear " + reviewers.name + "," + "<br>Please fill out the following survey " \
                                   "related to " + self.emp_id.name + "<br>Click here to access the survey.<br>" + \
                                   str(url) + "<br>Post your response for the appraisal till : " + str(self.appraisal_deadline)
                    values = {'model': 'hr.appraisal',
                              'res_id': self.ids[0],
                              'subject': survey_id.title,
                              'body_html': mail_content,
                              'parent_id': None,
                              'email_from': self.env.user.email or None,
                              'auto_delete': True,
                             }
                    values['email_to'] = reviewers.work_email
                    result = self.env['mail.mail'].create(values)._send()
                    if result is True:
                        send_count += 1
                        self.write({'tot_sent_survey': send_count})
                        rec = self.env['hr.appraisal.stages'].search([('sequence', '=', 2)])
                        self.state = rec.id
                        self.check_sent = True
                        self.check_draft = False

        if self.hr_emp and self.emp_survey_id:
            self.ensure_one()
            if not self.response_id:
                response = self.env['survey.user_input'].create(
                    {'survey_id': self.emp_survey_id.id, 'partner_id': self.emp_id.user_id.partner_id.id,
                     'appraisal_id': self.ids[0], 'deadline': self.appraisal_deadline, 'email': reviewers.user_id.email})
                self.response_id = response.id
            else:
                response = self.response_id
            return self.emp_survey_id.with_context(survey_token=response.token).action_start_survey()

    @api.multi
    def action_get_answers(self):
        """ This function will return all the answers posted related to this appraisal."""

        tree_res = self.env['ir.model.data'].get_object_reference('survey', 'survey_user_input_tree')
        tree_id = tree_res and tree_res[1] or False
        form_res = self.env['ir.model.data'].get_object_reference('survey', 'survey_user_input_form')
        form_id = form_res and form_res[1] or False
        return {
            'model': 'ir.actions.act_window',
            'name': 'Answers',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'survey.user_input',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'domain': [('state', '=', 'done'), ('appraisal_id', '=', self.ids[0])],

        }

    @api.one
    def _compute_completed_survey(self):

        answers = self.env['survey.user_input'].search([('state', '=', 'done'), ('appraisal_id', '=', self.ids[0])])
        self.tot_comp_survey = len(answers)


class AppraisalStages(models.Model):
    _name = 'hr.appraisal.stages'
    _description = 'Appraisal Stages'

    name = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence")
    fold = fields.Boolean(string='Folded in Appraisal Pipeline',
                          help='This stage is folded in the kanban view when '
                               'there are no records in that stage to display.')
