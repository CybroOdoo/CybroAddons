# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj(odoo@cybrosys.com)
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
#############################################################################
import requests
from requests.exceptions import RequestException
import werkzeug
from odoo import api, fields, models


class SurveyWhatsapp(models.TransientModel):
    """ Share content to multiple whatsapp number."""
    _name = 'survey.whatsapp'
    _description = "Survey Whatsapp"

    partner_ids = fields.Many2many('res.partner',
                                   string="Recipient",
                                   required=True,
                                   help="Recipients for whatsapp message")
    message = fields.Text(string="Message",
                          default=f"""Dear Participants,\n\n We are conducting a survey and your respond would be appreciable.Please answer the following survey""",
                          required=True,
                          help="Message body for whatsapp message")
    survey_start_url = fields.Char('Survey URL',
                                   compute='_compute_survey_start_url',
                                   required=True,
                                   help="Url for starting survey")
    answer_dead_line = fields.Date(string="Answer Dead Line",
                                   required=True,
                                   help="Deadline for getting answer")
    survey_id = fields.Many2one('survey.survey',
                                string='Survey',
                                required=True,
                                help="Survey name")

    @api.depends('survey_id')
    def _compute_survey_start_url(self):
        """Automatically fill url of survey"""
        for invite in self:
            invite.survey_start_url = werkzeug.urls.url_join(
                invite.survey_id.get_base_url(),
                invite.survey_id.get_start_url()) if invite.survey_id else False

    def action_send_msg(self):
        """Send content to whatsapp number."""
        for partner in self.partner_ids:
            if self.message and partner.mobile:
                instant = self.env['configuration.manager'].search(
                    [('state', '=', 'verified')], limit=1)
                if instant:
                    url = "https://api.apichat.io/instance" + instant.instance + "/sendMessage?token=" + instant.token
                    sent_message = self.message + "\n\n" + self.survey_start_url + "\n\n" + 'Before' + "\t" + str(
                        self.answer_dead_line)
                    data = {
                        "phone": int(
                            partner.mobile.replace('-', '').replace('(',
                                                                    "").replace(
                                ')', '').replace(' ', '')),
                        "body": sent_message
                    }
                    try:
                        response = requests.post(url, json=data, timeout=30)
                        response.raise_for_status()
                    except RequestException as e:
                        return {'status': 'error', 'message': str(e)}
                    self.env['whatsapp.message'].create({
                        'status': 'sent',
                        'from_user': self.env.user.id,
                        'to_user': partner.mobile,
                        'body': sent_message
                    })
