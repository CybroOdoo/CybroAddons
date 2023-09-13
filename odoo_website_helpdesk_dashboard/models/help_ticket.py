# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
import calendar
from odoo import api, models


class HelpDeskTicket(models.Model):
    """HelpDeskTicket class helps to create new tickets and inside this class
     it will show the tickets with different stages. Get ticket information
     easily."""
    _inherit = 'help.ticket'

    @api.model
    def check_user_group(self):
        """Checking user group"""
        return self.env.user.has_group('base.group_user')

    @api.model
    def get_tickets_count(self):
        """Get the count of tickets based on their stages."""
        values = {
            'inbox_count': self.env['help.ticket'].search_count(
                [('stage_id.name', 'in', ['Inbox', 'Draft'])]),
            'progress_count': self.env['help.ticket'].search_count(
                [('stage_id.name', '=', 'In Progress')]),
            'done_count': self.env['help.ticket'].search_count(
                [('stage_id.name', '=', 'Done')]),
            'team_count': self.env['help.team'].search_count([]),
            'p_tickets': [ticket.name for ticket in
                          self.env['help.ticket'].search(
                              [('stage_id.name', 'in', ['Inbox', 'Draft'])])]
        }
        return values

    @api.model
    def get_tickets_view(self):
        """Get detailed information about tickets."""
        values = {
            'inbox_count': self.env['help.ticket'].search_count(
                [('stage_id.name', 'in', ['Inbox', 'Draft'])]),
            'progress_count': self.env['help.ticket'].search_count(
                [('stage_id.name', '=', 'In Progress')]),
            'done_count': self.env['help.ticket'].search_count(
                [('stage_id.name', '=', 'Done')]),
            'team_count': self.env['help.team'].search_count([]),
            'new_tkts': ["{} : {}".format(ticket.name, ticket.subject) for
                         ticket in self.env['help.ticket'].search(
                    [('stage_id.name', 'in', ['Inbox', 'Draft'])])],
            'progress': ["{} : {}".format(ticket.name, ticket.subject) for
                         ticket in self.env['help.ticket'].search(
                    [('stage_id.name', '=', 'In Progress')])],
            'done': ["{} : {}".format(ticket.name, ticket.subject) for ticket in
                     self.env['help.ticket'].search(
                         [('stage_id.name', '=', 'Done')])],
            'teams': [team.name for team in self.env['help.team'].search([])],
            'p_tickets': [ticket.name for ticket in
                          self.env['help.ticket'].search(
                              [('stage_id.name', 'in', ['Inbox', 'Draft'])])]
        }
        return values

    @api.model
    def get_ticket_month_pie(self):
        """Get ticket counts per month as a pie chart."""
        month_count = [rec.create_date.month for rec in
                       self.env['help.ticket'].search([])]
        month_value = list(set(month_count))
        month_val = [{'label': calendar.month_name[month],
                      'value': month_count.count(month)} for month in
                     month_value]
        name = [record['label'] for record in month_val]
        count = [record['value'] for record in month_val]
        return [count, name]

    @api.model
    def get_team_ticket_count_pie(self):
        """Get ticket counts per team as a bar chart"""
        ticket_count = []
        team_list = []
        for rec in self.env['help.ticket'].search([]):
            if rec.team_id:
                team = rec.team_id.name
                if team not in team_list:
                    team_list.append(team)
                ticket_count.append(team)
        team_val = [{'label': team_name, 'value': ticket_count.count(team_name)}
                    for team_name in team_list]
        return [[record['value'] for record in team_val],
                [record['label'] for record in team_val]]

    @api.model
    def get_project_ticket_count(self):
        """Get ticket counts per project as a bar chart"""
        ticket_count = []
        project_list = []
        for rec in self.env['help.ticket'].search([]):
            if rec.project_id:
                project = rec.project_id.name
                if project not in project_list:
                    project_list.append(project)
                ticket_count.append(project)
        project_val = [
            {'label': project_name, 'value': ticket_count.count(project_name)}
            for project_name in project_list]
        project = [[record['value'] for record in project_val],
                   [record['label'] for record in project_val]]
        return project

    @api.model
    def get_billed_task_team_chart(self):
        """Get billed task counts per team as a polarArea chart"""
        ticket_count = []
        team_list = []
        tasks = [rec.ticket_id.id for rec in self.env['project.task'].search(
            [('ticket_billed', '=', True)])]
        for rec in self.env['help.ticket'].search([('id', 'in', tasks)]):
            team = rec.team_id.name
            if team not in team_list:
                team_list.append(team)
            ticket_count.append(team)
        team_val = [{'label': team_name, 'value': ticket_count.count(team_name)}
                    for team_name in team_list]
        return [[record['value'] for record in team_val],
                [record['label'] for record in team_val]]

    @api.model
    def get_team_ticket_done_pie(self):
        """Get ticket counts per completed tickets as a bar chart"""
        ticket_count = []
        team_list = []
        for rec in self.env['help.ticket'].search(
                [('stage_id.name', '=', 'Done')]):
            if rec.team_id:
                team = rec.team_id.name
                if team not in team_list:
                    team_list.append(team)
                ticket_count.append(team)
        team_val = [{'label': team_name, 'value': ticket_count.count(team_name)}
                    for team_name in team_list]
        return [[record['value'] for record in team_val],
                [record['label'] for record in team_val]]
