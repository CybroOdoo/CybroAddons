# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, api
import calendar


class HelpDeskTicket(models.Model):
    _inherit = 'help.ticket'

    @api.model
    def check_user_group(self):
        """Checking user group"""
        user = self.env.user
        if user.has_group('base.group_user'):
            return True
        else:
            return False

    @api.model
    def get_tickets_count(self):
        tickets_new_count = self.env['help.ticket'].search_count(
            [('stage_id.name', 'in', ['Inbox', 'Draft'])])
        tickets_in_progress_count = self.env['help.ticket'].search_count(
            [('stage_id.name', '=', 'In Progress')])
        tickets_closed_count = self.env['help.ticket'].search_count(
            [('stage_id.name', '=', 'Done')])
        teams_count = self.env['help.team'].search_count([])

        tickets = self.env['help.ticket'].search(
            [('stage_id.name', 'in', ['Inbox', 'Draft'])])
        p_tickets = []
        for ticket in tickets:
            p_tickets.append(ticket.name)

        values = {
            'inbox_count': tickets_new_count,
            'progress_count': tickets_in_progress_count,
            'done_count': tickets_closed_count,
            'team_count': teams_count,
            'p_tickets': p_tickets
        }
        return values

    @api.model
    def get_tickets_view(self):
        tickets_new_count = self.env['help.ticket'].search_count(
            [('stage_id.name', 'in', ['Inbox', 'Draft'])])
        tickets_in_progress_count = self.env['help.ticket'].search_count(
            [('stage_id.name', '=', 'In Progress')])
        tickets_closed_count = self.env['help.ticket'].search_count(
            [('stage_id.name', '=', 'Done')])
        teams_count = self.env['help.team'].search_count([])

        tickets_new = self.env['help.ticket'].search(
            [('stage_id.name', 'in', ['Inbox', 'Draft'])])
        tickets_in_progress = self.env['help.ticket'].search(
            [('stage_id.name', '=', 'In Progress')])
        tickets_closed = self.env['help.ticket'].search(
            [('stage_id.name', '=', 'Done')])
        teams = self.env['help.team'].search([])

        new_list = []
        progress_list = []
        done_list = []
        teams_list = []

        for new in tickets_new:
            new_list.append(str(new.name) + ' : ' + str(new.subject))
        for progress in tickets_in_progress:
            progress_list.append(
                str(progress.name) + ' : ' + str(progress.subject))
        for done in tickets_closed:
            done_list.append(str(done.name) + ' : ' + str(done.subject))
        for team in teams:
            teams_list.append(team.name)

        tickets = self.env['help.ticket'].search(
            [('stage_id.name', 'in', ['Inbox', 'Draft'])])
        p_tickets = []
        for ticket in tickets:
            p_tickets.append(ticket.name)

        values = {
            'inbox_count': tickets_new_count,
            'progress_count': tickets_in_progress_count,
            'done_count': tickets_closed_count,
            'team_count': teams_count,

            'new_tkts': new_list,
            'progress': progress_list,
            'done': done_list,
            'teams': teams_list,
            'p_tickets': p_tickets
        }
        return values

    @api.model
    def get_ticket_month_pie(self):
        """pie chart"""
        month_count = []
        month_value = []
        tickets = self.env['help.ticket'].search([])
        for rec in tickets:
            month = rec.create_date.month
            if month not in month_value:
                month_value.append(month)
            month_count.append(month)

        month_val = []
        for index in range(len(month_value)):
            value = month_count.count(month_value[index])
            month_name = calendar.month_name[month_value[index]]
            month_val.append({'label': month_name, 'value': value})

        name = []
        for record in month_val:
            name.append(record.get('label'))

        count = []
        for record in month_val:
            count.append(record.get('value'))

        month = [count, name]
        return month

    @api.model
    def get_team_ticket_count_pie(self):
        """bar chart"""
        ticket_count = []
        team_list = []
        tickets = self.env['help.ticket'].search([])

        for rec in tickets:
            if rec.team_id:
                team = rec.team_id.name
                if team not in team_list:
                    team_list.append(team)
                ticket_count.append(team)

        team_val = []
        for index in range(len(team_list)):
            value = ticket_count.count(team_list[index])
            team_name = team_list[index]
            team_val.append({'label': team_name, 'value': value})
        name = []
        for record in team_val:
            name.append(record.get('label'))
        #
        count = []
        for record in team_val:
            count.append(record.get('value'))
        #
        team = [count, name]
        return team

    @api.model
    def get_project_ticket_count(self):
        """bar chart"""
        ticket_count = []
        project_list = []
        tickets = self.env['help.ticket'].search([])

        for rec in tickets:
            if rec.project_id:
                project = rec.project_id.name
                if project not in project_list:
                    project_list.append(project)
                ticket_count.append(project)

        project_val = []
        for index in range(len(project_list)):
            value = ticket_count.count(project_list[index])
            project_name = project_list[index]
            project_val.append({'label': project_name, 'value': value})
        name = []
        for record in project_val:
            name.append(record.get('label'))
        #
        count = []
        for record in project_val:
            count.append(record.get('value'))
        #
        project = [count, name]
        return project

    @api.model
    def get_billed_task_team_chart(self):
        """polarArea chart"""
        ticket_count = []
        team_list = []
        tasks=[]
        project_task = self.env['project.task'].search([('ticket_billed', '=', True)])
        for rec in project_task:
            tasks.append(rec.ticket_id.id)
        tickets = self.env['help.ticket'].search([('id', 'in', tasks)])


        for rec in tickets:
            # if rec.id in teams.ids:
            team = rec.team_id.name
            if team not in team_list:
                team_list.append(team)
            ticket_count.append(team)

        team_val = []
        for index in range(len(team_list)):
            value = ticket_count.count(team_list[index])
            team_name = team_list[index]
            team_val.append({'label': team_name, 'value': value})
        name = []
        for record in team_val:
            name.append(record.get('label'))
        #
        count = []
        for record in team_val:
            count.append(record.get('value'))
        #
        team = [count, name]
        return team

    @api.model
    def get_team_ticket_done_pie(self):
        """bar chart"""
        ticket_count = []
        team_list = []
        tickets = self.env['help.ticket'].search(
            [('stage_id.name', '=', 'Done')])

        for rec in tickets:
            if rec.team_id:
                team = rec.team_id.name
                if team not in team_list:
                    team_list.append(team)
                ticket_count.append(team)

        team_val = []
        for index in range(len(team_list)):
            value = ticket_count.count(team_list[index])
            team_name = team_list[index]
            team_val.append({'label': team_name, 'value': value})
        name = []
        for record in team_val:
            name.append(record.get('label'))
        #
        count = []
        for record in team_val:
            count.append(record.get('value'))
        #
        team = [count, name]
        return team
