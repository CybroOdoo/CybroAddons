# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

MAX_ACTIVITY_SUMMARY = 200


class AiChatConversation(models.Model):
    """ The next steps of a deep analysis planned as activities of Odoo: activities of the
    user asking, not linked to a record (conversations are private), whose note links
    back to the analysis. """
    _inherit = 'ai.chat.conversation'

    @api.model
    def get_next_step_activity_defaults(self, message_id, step_index):
        """ What the confirmation of a next step to plan proposes: its summary, the types of
        activity and the due date each one gives. """
        _message, step = self._get_next_step(message_id, step_index)
        types = self._get_next_step_activity_types()
        todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        default_type = todo if todo in types else types[:1]
        return {
            'summary': step[:MAX_ACTIVITY_SUMMARY],
            'activity_type_id': default_type.id,
            'activity_types': [{
                'id': activity_type.id,
                'name': activity_type.name,
                'icon': activity_type.icon or 'fa-tasks',
                'date_deadline': fields.Date.to_string(activity_type._get_date_deadline()),
            } for activity_type in types],
            'user_name': self.env.user.name,
        }

    @api.model
    def create_next_step_activity(self, message_id, step_index, values):
        """ Plan a next step of a deep analysis as an activity of the current user.

        :param dict values: ``summary``, ``activity_type_id`` and ``date_deadline``
            confirmed by the user
        :return: the analysis, with the activity planned
        """
        message, step = self._get_next_step(message_id, step_index, lock=True)
        planned = dict(message.result.get('next_step_activities') or {})
        if planned.get(str(step_index)) and self.env['mail.activity'].sudo().browse(
                planned[str(step_index)]).exists().active:
            raise UserError(self.env._("This step is already planned as an activity."))
        activity_type = self._get_next_step_activity_types().filtered(
            lambda t: t.id == (values or {}).get('activity_type_id'))
        if not activity_type:
            raise UserError(self.env._("Please choose a type of activity."))
        try:
            date_deadline = fields.Date.to_date((values or {}).get('date_deadline')) or activity_type._get_date_deadline()
        except ValueError:
            raise UserError(self.env._("The due date is not valid."))
        summary = str((values or {}).get('summary') or '').strip()[:MAX_ACTIVITY_SUMMARY] or step[:MAX_ACTIVITY_SUMMARY]
        activity = self.env['mail.activity'].create({
            'activity_type_id': activity_type.id,
            'summary': summary,
            'date_deadline': date_deadline,
            'user_id': self.env.uid,
            'note': self._get_next_step_note(message, step),
        })
        planned[str(step_index)] = activity.id
        # the messages are not written by their users: the activity is kept as the assistant
        message.sudo().result = {**message.result, 'next_step_activities': planned}
        return message._get_chat_values()

    @api.model
    def _get_next_step(self, message_id, step_index, lock=False):
        """ A next step of a deep analysis of the current user. """
        self._check_chat_access()
        message = self.env['ai.chat.message'].browse(message_id).exists()
        if not message or message.conversation_id.user_id != self.env.user:
            raise AccessError(self.env._("This message does not exist or is not yours."))
        if lock:
            # a step is planned once, even if confirmed twice at the same time
            self.env.cr.execute("SELECT id FROM ai_chat_message WHERE id = %s FOR UPDATE", [message.id])
            message.invalidate_recordset(['result'])
        analysis = message.result or {}
        steps = analysis.get('next_steps') or []
        if analysis.get('type') != 'analysis' or not isinstance(step_index, int) or not 0 <= step_index < len(steps):
            raise UserError(self.env._("This answer has no such next step."))
        return message, steps[step_index]

    @api.model
    def _get_next_step_activity_types(self):
        """ The types of activity that need no record to be linked to. """
        return self.env['mail.activity.type'].search([('res_model', '=', False)])

    @api.model
    def _get_next_step_note(self, message, step):
        """ The note of a planned step: the question and decision it comes from, and a link
        back to the analysis. """
        question = self.env['ai.chat.message'].search([
            ('conversation_id', '=', message.conversation_id.id), ('role', '=', 'user'), ('id', '<', message.id),
        ], order='id desc', limit=1).content or message.conversation_id.name
        verdict = (message.result or {}).get('verdict') or ''
        # the action of the menu, so that the app of the assistant is shown, with the conversation
        url = f"/odoo/action-ai_chat_pro.ai_chat_action_client?active_id={message.conversation_id.id}"
        note = Markup("<p>%s</p>") % self.env._("Next step of the deep analysis of \"%s\".", question)
        if verdict:
            note += Markup("<p><strong>%s</strong> %s</p>") % (self.env._("Decision:"), verdict)
        note += Markup('<p><a href="%s">%s</a></p>') % (url, self.env._("Open the analysis"))
        return note


class AiChatMessage(models.Model):
    _inherit = 'ai.chat.message'

    def _get_chat_values(self):
        values = super()._get_chat_values()
        result = values.get('result')
        if isinstance(result, dict) and result.get('type') == 'analysis' and result.get('next_step_activities'):
            values['result'] = {**result, 'next_step_activities': self._get_next_step_activities(result)}
        return values

    def _get_next_step_activities(self, result):
        """ The activities planned for the next steps of an analysis, as they are now: done
        ones are archived, removed ones are left out (the step can be planned again). """
        planned = {index: activity_id for index, activity_id in result['next_step_activities'].items() if activity_id}
        # the message is readable: the state of its activities is shown, whoever they are assigned to
        activities = self.env['mail.activity'].sudo().with_context(active_test=False).browse(
            list(planned.values())).exists()
        by_id = {activity.id: activity for activity in activities}
        shown = {}
        for index, activity_id in planned.items():
            if activity := by_id.get(activity_id):
                shown[index] = {
                    'id': activity.id,
                    'state': activity.state if activity.active else 'done',
                    'date_deadline': fields.Date.to_string(activity.date_deadline),
                    'type': activity.activity_type_id.name or '',
                    'icon': activity.activity_type_id.icon or 'fa-tasks',
                }
        return shown
