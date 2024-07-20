# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import calendar
from odoo import api, models


class TicketHelpdesk(models.Model):
    """ Inherited class to get help desk ticket details...."""
    _inherit = 'ticket.helpdesk'

    @api.model
    def check_user_group(self):
        """Checking user group"""
        user = self.env.user
        if user.has_group('base.group_user'):
            return True
        return False

    @api.model
    def get_tickets_count(self):
        """ Function To Get The Ticket Count"""
        ticket_details = self.env['ticket.helpdesk'].search([])
        ticket_data = []
        for ticket in ticket_details:
            ticket_data.append({
                'ticket_name': ticket.name,
                'customer_name': ticket.customer_id.name,
                'subject': ticket.subject,
                'priority': ticket.priority,
                'assigned_to': ticket.assigned_user_id.name,
                'assigned_image': ticket.assigned_user_id.image_1920,
            })
        tickets_new_count = self.env['ticket.helpdesk'].search_count(
            [('stage_id.name', 'in', ['Inbox', 'Draft'])])
        tickets_in_progress_count = self.env['ticket.helpdesk'].search_count(
            [('stage_id.name', '=', 'In Progress')])
        tickets_closed_count = self.env['ticket.helpdesk'].search_count(
            [('stage_id.name', '=', 'Done')])
        very_low_count = self.env['ticket.helpdesk'].search_count([
            ('priority', '=', '0')])
        very_low_count1 = very_low_count * 10
        low_count = self.env['ticket.helpdesk'].search_count([
            ('priority', '=', '1')])
        low_count1 = low_count * 10
        normal_count = self.env['ticket.helpdesk'].search_count([
            ('priority', '=', '2')])
        normal_count1 = normal_count * 10
        high_count = self.env['ticket.helpdesk'].search_count([
            ('priority', '=', '3')])
        high_count1 = high_count * 10
        very_high_count = self.env['ticket.helpdesk'].search_count([
            ('priority', '=', '4')])
        very_high_count1 = very_high_count * 10
        response = self.env['ticket.helpdesk'].search_count([
            ('review', '!=', None)])
        teams_count = self.env['team.helpdesk'].search_count([])
        tickets = self.env['ticket.helpdesk'].search(
            [('stage_id.name', 'in', ['Inbox', 'Draft'])])
        p_tickets = []
        for ticket in tickets:
            p_tickets.append(ticket.name)
        values = {
            'inbox_count': tickets_new_count,
            'progress_count': tickets_in_progress_count,
            'done_count': tickets_closed_count,
            'team_count': teams_count,
            'p_tickets': p_tickets,
            'very_low_count1': very_low_count1,
            'low_count1': low_count1,
            'normal_count1': normal_count1,
            'high_count1': high_count1,
            'very_high_count1': very_high_count1,
            'response': response,
            'ticket_details': ticket_data,
        }
        return values

    @api.model
    def get_tickets_view(self):
        """ Function To Get The Ticket View"""
        tickets_new_count = self.env['ticket.helpdesk'].search_count(
            [('stage_id.name', 'in', ['Inbox', 'Draft'])])
        tickets_in_progress_count = self.env['ticket.helpdesk'].search_count(
            [('stage_id.name', '=', 'In Progress')])
        tickets_closed_count = self.env['ticket.helpdesk'].search_count(
            [('stage_id.name', '=', 'Done')])
        teams_count = self.env['team.helpdesk'].search_count([])
        tickets_new = self.env['ticket.helpdesk'].search(
            [('stage_id.name', 'in', ['Inbox', 'Draft'])])
        tickets_in_progress = self.env['ticket.helpdesk'].search(
            [('stage_id.name', '=', 'In Progress')])
        tickets_closed = self.env['ticket.helpdesk'].search(
            [('stage_id.name', '=', 'Done')])
        teams = self.env['team.helpdesk'].search([])
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
        tickets = self.env['ticket.helpdesk'].search(
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
        """For pie chart"""
        month_count = []
        month_value = []
        tickets = self.env['ticket.helpdesk'].search([])
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
        """For bar chart"""
        ticket_count = []
        team_list = []
        tickets = self.env['ticket.helpdesk'].search([])
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
        count = []
        for record in team_val:
            count.append(record.get('value'))
        team = [count, name]
        return team
