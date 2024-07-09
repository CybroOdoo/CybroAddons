# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu K P(odoo@cybrosys.com)
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


class SurveySurvey(models.Model):
    """Inherited this model for adding schedule operation"""
    _inherit = 'survey.survey'

    is_cron = fields.Boolean(string='Enable Cron',
                             help='Enable cron action for schedule survey')
    scheduled_date = fields.Date(
        string='Scheduled Date',
        help='Choose the schedule date for this survey')
    cron_status = fields.Selection([
        ('done', 'Done'), ('in_progress', 'In Progress')],
        help='Status of this survey', string='Cron Status',  readonly=True,
        copy= False)
    contact_ids = fields.Many2many('res.partner',
                                   string='Existing contacts',
                                   help='Choose or create the participants')

    @api.onchange('scheduled_date')
    def _onchange_scheduled_date(self):
        """Status of the schedule action"""
        if self.scheduled_date and self.scheduled_date >= fields.date.today():
            self.write({'cron_status': 'in_progress'})

    def send_scheduled_survey(self):
        """Email sending schedule action"""
        # Find surveys that are scheduled for today
        # and have not been processed yet
        surveys = self.env['survey.survey'].search(
            [('is_cron', '=', True),
             ('scheduled_date', '=', fields.date.today()),
             ('cron_status', '!=', 'done')])
        for survey in surveys:
            # Get the email template for inviting
            # users to participate in the survey
            template = self.env.ref('survey.mail_template_user_input_invite')
            # Prepare the local context for creating the survey invites
            local_context = dict(
                self.env.context,
                default_survey_id=survey.id,
                default_use_template=bool(template),
                default_template_id=template and template.id or False,
                notif_layout='mail.mail_notification_light',
            )
            # Create survey invites for each contact
            record = self.env["survey.invite"].sudo().with_context(
                local_context).create(
                {'partner_ids': [(4, i)
                                 for i in survey.mapped('contact_ids').ids]})
            record.action_invite()
            survey.sudo().write({
                'cron_status': 'done'
            })
