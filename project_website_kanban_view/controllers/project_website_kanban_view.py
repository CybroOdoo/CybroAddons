# -*- coding: utf-8 -*-
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
import copy

from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class ProjectCustomerPortal(CustomerPortal):
    """
    This class extends the CustomerPortal class in Odoo and provides
    custom functionality for managing projects and tasks from the
    customer portal.
    """

    def _prepare_tasks_values(self, page, date_begin, date_end, sortby, search,
                              search_in, groupby, url="/my/tasks", domain=None,
                              su=False, project=False):
        """
        Prepare the values for displaying tasks in the customer portal.

        :param page: Current page number.
        :param date_begin: Beginning of date range filter.
        :param date_end: End of date range filter.
        :param sortby: Sorting option.
        :param search: Search keyword.
        :param search_in: Field to search in (e.g., name).
        :param groupby: Grouping option.
        :param url: URL for the tasks page.
        :param domain: Filter domain for tasks.
        :return: Dictionary containing values for tasks display.
        """
        task_per_page = request.env['ir.config_parameter'].sudo().get_int(
            'project_website_kanban_view.task_per_pager', default=80)
        if task_per_page <= 0:
            task_per_page = 80

        # Avoid mutating self._items_per_page on the shared controller singleton.
        proxy = copy.copy(self)
        proxy._items_per_page = task_per_page

        values = super(ProjectCustomerPortal, proxy)._prepare_tasks_values(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby,
            search=search, search_in=search_in, groupby=groupby, url=url,
            domain=domain, su=su, project=project)
        if 'pager' in values and 'url_args' in values['pager']:
            viewtype = request.params.get('viewtype')
            if viewtype:
                values['pager']['url_args']['viewtype'] = viewtype
        return values

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
        :return: HTTP response.
        """
        res = super().portal_my_projects(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby,
            **kw)
        if hasattr(res, 'qcontext'):
            res.qcontext['viewtype'] = viewtype
        return res

    @http.route(['/my/tasks', '/my/tasks/page/<int:page>'], type='http',
                auth="user", website=True)
    def portal_my_tasks(self, page=1, date_begin=None, date_end=None,
                        sortby=None, filterby=None, search=None,
                        search_in='name', groupby=None, viewtype='kanban',
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
        :param search_in: Field to search in (e.g., name).
        :param groupby: Grouping option.
        :param viewtype: Type of view to display (e.g., kanban).
        :return: HTTP response with the task details.
        """
        res = super().portal_my_tasks(
            page=page, date_begin=date_begin, date_end=date_end,
            sortby=sortby, filterby=filterby, search=search,
            search_in=search_in, groupby=groupby, **kw)
        if hasattr(res, 'qcontext'):
            res.qcontext['viewtype'] = viewtype
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
        res = super().portal_my_project(
            project_id=project_id, access_token=access_token, page=page,
            date_begin=date_begin, date_end=date_end, sortby=sortby,
            search=search, search_in=search_in, groupby=groupby,
            task_id=task_id, **kw)
        if hasattr(res, 'qcontext'):
            res.qcontext['viewtype'] = viewtype
        return res
