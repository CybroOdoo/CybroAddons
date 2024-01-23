# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import datetime as DT
from odoo import http
from odoo.http import request


class HelpDeskDashboard(http.Controller):
    """Website helpdesk dashboard"""

    @http.route(['/helpdesk_dashboard'], type='json', auth="public")
    def helpdesk_dashboard(self):
        """Helpdesk dashboard controller"""
        stage_new = request.env['ticket.stage'].search(
            [('name', '=', 'Inbox')], limit=1).id
        stage_draft = request.env['ticket.stage'].search(
            [('name', '=', 'Draft')], limit=1).id
        stage_inprogress = request.env['ticket.stage'].search(
            [('name', '=', 'In Progress')], limit=1).id
        stage_canceled = request.env['ticket.stage'].search(
            [('name', '=', 'Canceled')], limit=1).id
        stage_done = request.env['ticket.stage'].search(
            [('name', '=', 'Done')], limit=1).id
        stage_closed = request.env['ticket.stage'].search(
            [('name', '=', 'Closed')], limit=1).id
        stage_ids = [stage_new, stage_draft]
        new = request.env["help.ticket"].search_count(
            [('stage_id', 'in', stage_ids)])
        new_id = request.env["help.ticket"].search(
            [('stage_id', 'in', stage_ids)])
        new_id_ls = [data.id for data in new_id]
        in_progress = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_inprogress)])
        in_progress_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_inprogress)])
        in_progress_ls = [data.id for data in in_progress_id]
        canceled = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_canceled)])
        canceled_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_canceled)])
        canceled_id_ls = [data.id for data in canceled_id]
        done = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_done)])
        done_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_done)])
        done_id_ls = [data.id for data in done_id]
        closed = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_closed)])
        closed_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_closed)])
        closed_id_ls = [data.id for data in closed_id]
        dashboard_values = {
            'new': new,
            'in_progress': in_progress,
            'canceled': canceled,
            'done': done,
            'closed': closed,
            'new_id': new_id_ls,
            'in_progress_id': in_progress_ls,
            'canceled_id': canceled_id_ls,
            'done_id': done_id_ls,
            'closed_id': closed_id_ls,
        }
        return dashboard_values

    @http.route(['/helpdesk_dashboard_week'], type='json', auth="public")
    def helpdesk_dashboard_week(self):
        """Week based sorting controller"""
        today = DT.date.today()
        stage_new = request.env['ticket.stage'].search(
            [('name', '=', 'Inbox')], limit=1).id
        stage_draft = request.env['ticket.stage'].search(
            [('name', '=', 'Draft')], limit=1).id
        stage_inprogress = request.env['ticket.stage'].search(
            [('name', '=', 'In Progress')], limit=1).id
        stage_canceled = request.env['ticket.stage'].search(
            [('name', '=', 'Canceled')], limit=1).id
        stage_done = request.env['ticket.stage'].search(
            [('name', '=', 'Done')], limit=1).id
        stage_closed = request.env['ticket.stage'].search(
            [('name', '=', 'Closed')], limit=1).id
        stage_ids = [stage_new, stage_draft]
        week_ago = str(today - DT.timedelta(days=7)) + ' '
        new = request.env["help.ticket"].search_count(
            [('stage_id', 'in', stage_ids), ('create_date', '>', week_ago)])
        new_id = request.env["help.ticket"].search(
            [('stage_id', 'in', stage_ids), ('create_date', '>', week_ago)])
        new_id_ls = [data.id for data in new_id]
        in_progress = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_inprogress),
             ('create_date', '>', week_ago)])
        in_progress_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_inprogress),
             ('create_date', '>', week_ago)])
        in_progress_ls = [data.id for data in in_progress_id]
        canceled = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_canceled),
             ('create_date', '>', week_ago)])
        canceled_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_canceled),
             ('create_date', '>', week_ago)])
        canceled_id_ls = [data.id for data in canceled_id]
        done = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_done), ('create_date', '>', week_ago)])
        done_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_done), ('create_date', '>', week_ago)])
        done_id_ls = [data.id for data in done_id]
        closed = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_closed), ('create_date', '>', week_ago)])
        closed_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_closed), ('create_date', '>', week_ago)])
        closed_id_ls = [data.id for data in closed_id]
        dashboard_values = {
            'new': new,
            'in_progress': in_progress,
            'canceled': canceled,
            'done': done,
            'closed': closed,
            'new_id': new_id_ls,
            'in_progress_id': in_progress_ls,
            'canceled_id': canceled_id_ls,
            'done_id': done_id_ls,
            'closed_id': closed_id_ls,
        }
        return dashboard_values

    @http.route(['/helpdesk_dashboard_month'], type='json', auth="public")
    def helpdesk_dashboard_month(self):
        """Month based sorting controller"""
        today = DT.date.today()
        stage_new = request.env['ticket.stage'].search(
            [('name', '=', 'Inbox')], limit=1).id
        stage_draft = request.env['ticket.stage'].search(
            [('name', '=', 'Draft')], limit=1).id
        stage_inprogress = request.env['ticket.stage'].search(
            [('name', '=', 'In Progress')], limit=1).id
        stage_canceled = request.env['ticket.stage'].search(
            [('name', '=', 'Canceled')], limit=1).id
        stage_done = request.env['ticket.stage'].search(
            [('name', '=', 'Done')], limit=1).id
        stage_closed = request.env['ticket.stage'].search(
            [('name', '=', 'Closed')], limit=1).id
        stage_ids = [stage_new, stage_draft]
        week_ago = str(today - DT.timedelta(days=30)) + ' '
        new = request.env["help.ticket"].search_count(
            [('stage_id', 'in', stage_ids), ('create_date', '>', week_ago)])
        new_id = request.env["help.ticket"].search(
            [('stage_id', 'in', stage_ids), ('create_date', '>', week_ago)])
        new_id_ls = [data.id for data in new_id]
        in_progress = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_inprogress),
             ('create_date', '>', week_ago)])
        in_progress_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_inprogress),
             ('create_date', '>', week_ago)])
        in_progress_ls = [data.id for data in in_progress_id]
        canceled = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_canceled),
             ('create_date', '>', week_ago)])
        canceled_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_canceled),
             ('create_date', '>', week_ago)])
        canceled_id_ls = [data.id for data in canceled_id]
        done = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_done), ('create_date', '>', week_ago)])
        done_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_done), ('create_date', '>', week_ago)])
        done_id_ls = [data.id for data in done_id]
        closed = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_closed), ('create_date', '>', week_ago)])
        closed_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_closed), ('create_date', '>', week_ago)])
        closed_id_ls = [data.id for data in closed_id]
        dashboard_values = {
            'new': new,
            'in_progress': in_progress,
            'canceled': canceled,
            'done': done,
            'closed': closed,
            'new_id': new_id_ls,
            'in_progress_id': in_progress_ls,
            'canceled_id': canceled_id_ls,
            'done_id': done_id_ls,
            'closed_id': closed_id_ls,
        }
        return dashboard_values

    @http.route(['/helpdesk_dashboard_year'], type='json', auth="public")
    def helpdesk_dashboard_year(self):
        """Year based sorting"""
        today = DT.date.today()
        stage_new = request.env['ticket.stage'].search(
            [('name', '=', 'Inbox')], limit=1).id
        stage_draft = request.env['ticket.stage'].search(
            [('name', '=', 'Draft')], limit=1).id
        stage_inprogress = request.env['ticket.stage'].search(
            [('name', '=', 'In Progress')], limit=1).id
        stage_canceled = request.env['ticket.stage'].search(
            [('name', '=', 'Canceled')], limit=1).id
        stage_done = request.env['ticket.stage'].search(
            [('name', '=', 'Done')], limit=1).id
        stage_closed = request.env['ticket.stage'].search(
            [('name', '=', 'Closed')], limit=1).id
        stage_ids = [stage_new, stage_draft]
        week_ago = str(today - DT.timedelta(days=360)) + ' '
        new = request.env["help.ticket"].search_count(
            [('stage_id', 'in', stage_ids), ('create_date', '>', week_ago)])
        new_id = request.env["help.ticket"].search(
            [('stage_id', 'in', stage_ids), ('create_date', '>', week_ago)])
        new_id_ls = [data.id for data in new_id]
        in_progress = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_inprogress),
             ('create_date', '>', week_ago)])
        in_progress_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_inprogress),
             ('create_date', '>', week_ago)])
        in_progress_ls = [data.id for data in in_progress_id]
        canceled = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_canceled),
             ('create_date', '>', week_ago)])
        canceled_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_canceled),
             ('create_date', '>', week_ago)])
        canceled_id_ls = [data.id for data in canceled_id]
        done = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_done), ('create_date', '>', week_ago)])
        done_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_done), ('create_date', '>', week_ago)])
        done_id_ls = [data.id for data in done_id]
        closed = request.env["help.ticket"].search_count(
            [('stage_id', '=', stage_closed), ('create_date', '>', week_ago)])
        closed_id = request.env["help.ticket"].search(
            [('stage_id', '=', stage_closed), ('create_date', '>', week_ago)])
        closed_id_ls = [data.id for data in closed_id]
        dashboard_values = {
            'new': new,
            'in_progress': in_progress,
            'canceled': canceled,
            'done': done,
            'closed': closed,
            'new_id': new_id_ls,
            'in_progress_id': in_progress_ls,
            'canceled_id': canceled_id_ls,
            'done_id': done_id_ls,
            'closed_id': closed_id_ls,
        }
        return dashboard_values
