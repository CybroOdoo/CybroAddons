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
#############################################################################
from odoo import api, fields, models
from odoo.orm.domains import Domain


class MailActivity(models.Model):
    """Inherited mail.activity model to add dashboard and tag functionalities."""
    _inherit = "mail.activity"

    activity_tag_ids = fields.Many2many(
        'activity.tag',
        string='Activity Tags',
        help='Select activity tags.',
    )
    state = fields.Selection(search='_search_state')

    def _search_state(self, operator, value):
        """Dynamic search domain mapping for activity state."""
        today = fields.Date.today()
        values = (
            set(value)
            if isinstance(value, (list, tuple, set, frozenset))
            or (hasattr(value, '__iter__') and not isinstance(value, str))
            else {value}
        )

        def domain_for_val(v):
            if v == 'done':
                return Domain([('active', '=', False)])
            if v == 'today':
                return Domain([('active', '=', True), ('date_deadline', '=', today)])
            if v == 'overdue':
                return Domain([('active', '=', True), ('date_deadline', '<', today)])
            if v == 'planned':
                return Domain([('active', '=', True), ('date_deadline', '>', today)])
            return Domain.FALSE

        if operator in ('=', 'in'):
            dom = Domain.FALSE
            for val in values:
                dom |= domain_for_val(val)
            return dom
        if operator in ('!=', 'not in'):
            dom = Domain.FALSE
            for val in values:
                dom |= domain_for_val(val)
            return ~dom
        return []

    def _action_done(self, feedback=False, attachment_ids=None):
        """Delegate to super _action_done which archives completed activities in Odoo 20."""
        return super()._action_done(feedback=feedback, attachment_ids=attachment_ids)

    @api.model
    def get_activity(self, activity_id=False):
        """Method for returning model and id of activity."""
        if not activity_id:
            return {}
        try:
            act_id = int(activity_id)
        except (ValueError, TypeError):
            return {}
        activity = self.browse(act_id)
        if not activity.exists():
            return {}
        return {
            'model': activity.res_model,
            'res_id': activity.res_id,
        }
