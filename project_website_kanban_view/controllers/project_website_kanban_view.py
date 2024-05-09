# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, \
    pager as portal_pager


class ProjectCustomerPortal(CustomerPortal):
    """
    This class extends the CustomerPortal class in Odoo and provides
    custom functionality for managing projects and tasks from the
    customer portal.
    """

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
        res.qcontext.update({'viewtype': viewtype})
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
        searchbar_filters = self._get_my_tasks_searchbar_filters()
        domain = searchbar_filters.get(filterby, searchbar_filters.get('all'))[
            'domain']
        values = self._prepare_tasks_values(page, date_begin, date_end, sortby,
                                            search, search_in, groupby,
                                            domain=domain)
        pager_vals = values['pager']
        pager_vals['url_args'].update(viewtype=viewtype)
        pager = portal_pager(**pager_vals)
        res.qcontext.update({
            'viewtype': viewtype,
            "pager": pager
        })
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
        return res

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
        :param search_in: Field to search in (e.g., content).
        :param groupby: Grouping option.
        :param url: URL for the tasks page.
        :param domain: Filter domain for tasks.
        :return: Dictionary containing values for tasks display.
        """
        res = super(ProjectCustomerPortal, self)._prepare_tasks_values(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby,
            search=search, search_in=search_in, groupby=groupby, url=url,
            domain=domain, su=su, project=project)
        task_per_page = int(
            request.env['ir.config_parameter'].sudo().get_param(
                "project_website_kanban_view.task_per_pager"))
        self._items_per_page = task_per_page
        if task_per_page == 0:
            raise ValidationError(_(
                "Task per page cannot be 0. Please configure a valid value."))
        return res
