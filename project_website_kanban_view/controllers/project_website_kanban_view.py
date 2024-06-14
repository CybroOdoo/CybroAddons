# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Mazlin AM (odoo@cybrosys.info)
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
from collections import OrderedDict
from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.osv.expression import OR, AND
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from odoo.addons.portal.controllers.portal import CustomerPortal, \
    pager as portal_pager


class ProjectCustomerPortal(CustomerPortal):
    """
    This class extends the CustomerPortal class in Odoo and provides
    custom functionality for managing projects and tasks from the
    customer portal.# def _project_get_page_view_values(self, project, access_token, page=1,
    #                                   date_begin=None, date_end=None,
    #                                   sortby=None, search=None,
    #                                   search_in='content', groupby=None,
    #                                   **kwargs):
    #     res = super(ProjectCustomerPortal, self)._project_get_page_view_values(
    #         project, access_token, page=page,
    #         date_begin=date_begin, date_end=date_end,
    #         sortby=sortby, search=search,
    #         search_in=search_in, groupby=groupby,
    #         **kwargs)
    #     print("thuis", self._items_per_page)
    #     task_per_page = int(
    #         request.env['ir.config_parameter'].sudo().get_param(
    #             "project_website_kanban_view.task_per_pager"))
    #     self._items_per_page = task_per_page
    #     if task_per_page == 0:
    #         raise ValidationError(_(
    #             "Task per page cannot be 0. Please configure a valid value."))
    #     return res
    """

    @http.route(['/my/project/<int:project_id>',
                 '/my/project/<int:project_id>/page/<int:page>',
                 '/my/project/<int:project_id>/task/<int:task_id>',
                 '/my/project/<int:project_id>/project_sharing'], type='http',
                auth="public")
    def portal_project_routes_outdated(self, **kwargs):
        """ Redirect the outdated routes to the new routes. """
        return request.redirect(
            request.httprequest.full_path.replace('/my/project/',
                                                  '/my/projects/'))

    @http.route(['/my/projects', '/my/projects/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_projects(
            self, page=1, date_begin=None, date_end=None, sortby=None,
            viewtype='kanban', **kw):
        """
        Route to display a list of projects for the logged-in user in the
        customer portal.
        :param page: Current page number.
        :param date_begin: Beginning of date range filter.
        :param date_end: End of date range filter.
        :param sortby: Sorting option.
        :param viewtype: Type of view to display (e.g., kanban).
        :return:
        """
        res = super(
            ProjectCustomerPortal, self).portal_my_projects(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby,
            viewtype='kanban',
            **kw)
        task_per_page = int(
            request.env['ir.config_parameter'].sudo().get_param(
                "project_website_kanban_view.task_per_pager"))
        self._items_per_page = task_per_page
        res.qcontext.update({'viewtype': viewtype})
        return res

    @http.route(['/my/projects/<int:project_id>',
                 '/my/projects/<int:project_id>/page/<int:page>'], type='http',
                auth="public", website=True)
    def portal_my_project(self, project_id=None, access_token=None, page=1,
                          date_begin=None, date_end=None, sortby=None,
                          search=None, search_in='content', groupby=None,
                          task_id=None, viewtype='kanban', **kw):
        """
        Route to display a specific project and its details in the customer
        portal.
        :param project_id: ID of the project to display.
        :param access_token: Access token for security.
        :param page: Current page number.
        :param date_begin: Beginning of date range filter.
        :param date_end: End of date range filter.
        :param sortby: Sorting option.
        :param search: Search keyword.
        :param search_in: Field to search in (e.g., content).
        :param groupby: Grouping option.
        :param task_id: ID of the task within the project.
        :param viewtype: Type of view to display (e.g., kanban).
        :return: HTTP response with the project details.
        """
        res = super(ProjectCustomerPortal, self).portal_my_project(
            project_id=project_id, access_token=access_token, page=page,
            date_begin=date_begin, date_end=date_end, sortby=sortby,
            search=search, search_in=search_in, groupby=groupby,
            task_id=task_id, viewtype='kanban', **kw)
        res.qcontext.update({'viewtype': viewtype})
        task_per_page = int(
            request.env['ir.config_parameter'].sudo().get_param(
                "project_website_kanban_view.task_per_pager"))
        self._items_per_page = task_per_page
        return res

    @http.route(['/my/tasks', '/my/tasks/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_tasks(self, page=1, date_begin=None, date_end=None,
                        sortby=None, filterby=None, search=None,
                        search_in='content', groupby=None, viewtype='kanban',
                        **kw):
        """
        Route to display a list of tasks for the logged-in user in the
        customer portal.
        :param page: Current page number.
        :param date_begin: Beginning of date range filter.
        :param date_end: End of date range filter.
        :param sortby: Sorting option.
        :param filterby: Filter option.
        :param search: Search keyword.
        :param search_in: Field to search in (e.g., content).
        :param groupby: Grouping option.
        :param viewtype: Type of view to display (e.g., kanban).
        :return: HTTP response with the project details.
        """

        res = super(ProjectCustomerPortal, self).portal_my_tasks(
            page=page, date_begin=date_begin, date_end=date_end,
            sortby=sortby, filterby=filterby, search=search,
            search_in=search_in, groupby=groupby, viewtype=viewtype, **kw)
        task_per_page = int(
            request.env['ir.config_parameter'].sudo().get_param(
                "project_website_kanban_view.task_per_pager"))
        self._items_per_page = task_per_page
        searchbar_sortings = dict(
            sorted(self._task_get_searchbar_sortings().items(),
                   key=lambda item: item[1]["sequence"]))
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('project_id', '!=', False)]},
        }
        projects = request.env['project.project'].search([])
        for project in projects:
            searchbar_filters.update({
                str(project.id): {'label': project.name,
                                  'domain': [('project_id', '=', project.id)]}
            })
        project_groups = request.env['project.task'].read_group(
            [('project_id', 'not in', projects.ids)],
            ['project_id'], ['project_id'])
        for group in project_groups:
            proj_id = group['project_id'][0] if group['project_id'] else False
            proj_name = group['project_id'][1] if group['project_id'] else _(
                'Others')
            searchbar_filters.update({
                str(proj_id): {'label': proj_name,
                               'domain': [('project_id', '=', proj_id)]}
            })
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        if not filterby:
            filterby = 'all'
        domain = searchbar_filters.get(filterby, searchbar_filters.get('all'))[
            'domain']
        if not groupby:
            groupby = 'project'
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin),
                       ('create_date', '<=', date_end)]
        if search and search_in:
            domain += self._task_get_search_domain(search_in, search)
        TaskSudo = request.env['project.task'].sudo()
        domain = AND([domain,
                      request.env['ir.rule']._compute_domain(TaskSudo._name,
                                                             'read')])
        task_count = TaskSudo.search_count(domain)
        pager = portal_pager(
            url="/my/tasks",
            url_args={'date_begin': date_begin, 'date_end': date_end,
                      'sortby': sortby, 'filterby': filterby,
                      'groupby': groupby, 'search_in': search_in,
                      'search': search, 'viewtype': viewtype},
            total=task_count,
            page=page,
            step=self._items_per_page
        )
        order = self._task_get_order(order, groupby)
        tasks = TaskSudo.search(domain, order=order, limit=self._items_per_page,
                                offset=pager['offset'])
        request.session['my_tasks_history'] = tasks.ids[:100]
        groupby_mapping = self._task_get_groupby_mapping()
        group = groupby_mapping.get(groupby)
        if group:
            grouped_tasks = [request.env['project.task'].concat(*g) for k, g in
                             groupbyelem(tasks, itemgetter(group))]
        else:
            grouped_tasks = [tasks] if tasks else []
        task_states = dict(request.env['project.task']._fields[
                               'kanban_state']._description_selection(
            request.env))
        if sortby == 'status':
            if groupby == 'none' and grouped_tasks:
                grouped_tasks[0] = grouped_tasks[0].sorted(
                    lambda tasks: task_states.get(tasks.kanban_state))
            else:
                grouped_tasks.sort(
                    key=lambda tasks: task_states.get(tasks[0].kanban_state))
        res.qcontext.update({
            'viewtype': viewtype,
            "pager": pager
        })
        return res

