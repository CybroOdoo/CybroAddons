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
from odoo import api, models

# Stages of the Website HelpDesk counted in each card of the dashboard
DASHBOARD_STAGES = {
    'new': ['stage_inbox', 'stage_draft'],
    'in_progress': ['stage_in_progress'],
    'done': ['stage_done'],
}
LATEST_TICKET_LIMIT = 10


class TicketHelpdesk(models.Model):
    """Add the data of the HelpDesk dashboard to the tickets."""
    _inherit = 'ticket.helpdesk'

    @api.model
    def _get_dashboard_stage_ids(self):
        """Return the stage ids counted in each card of the dashboard."""
        stage_ids = {}
        for key, xml_ids in DASHBOARD_STAGES.items():
            stage_ids[key] = [
                stage.id for stage in (
                    self.env.ref(f'odoo_website_helpdesk.{xml_id}',
                                 raise_if_not_found=False)
                    for xml_id in xml_ids)
                if stage]
        return stage_ids

    @api.model
    def get_dashboard_data(self):
        """Return the counters, the charts and the latest tickets shown on
        the dashboard, only from the tickets the user can read."""
        stage_ids = self._get_dashboard_stage_ids()
        counts = {
            key: self.search_count([('stage_id', 'in', ids)])
            for key, ids in stage_ids.items()
        }
        total = self.search_count([])
        priority_count = dict(self._read_group(
            [], ['priority'], ['__count']))
        priorities = [{
            'key': key,
            'label': label,
            'count': priority_count.get(key, 0),
            'percent': round(100 * priority_count.get(key, 0) / total)
            if total else 0,
        } for key, label in self._fields['priority']._description_selection(
            self.env)]
        team_count = self._read_group(
            [('team_id', '!=', False)], ['team_id'], ['__count'],
            order='__count desc')
        latest = self.search([], order='create_date desc, id desc',
                             limit=LATEST_TICKET_LIMIT)
        priority_labels = {item['key']: item['label'] for item in priorities}
        return {
            'stage_ids': stage_ids,
            'counts': counts,
            'team_count': self.env['team.helpdesk'].search_count([]),
            'review_count': self.search_count([('review', '!=', False)]),
            'priorities': priorities,
            'team_chart': {
                'labels': [team.display_name for team, _count in team_count],
                'values': [count for _team, count in team_count],
            },
            'tickets': [{
                'id': ticket.id,
                'name': ticket.name,
                'customer': ticket.customer_id.display_name
                or ticket.customer_name or '',
                'assigned_to': ticket.assigned_user_id.display_name or '',
                'subject': ticket.subject or '',
                'priority': priority_labels.get(ticket.priority, ''),
            } for ticket in latest],
        }
