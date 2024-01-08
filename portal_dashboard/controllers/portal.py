# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
from odoo.http import request, route
from odoo.addons.portal.controllers.portal import CustomerPortal


class DashboardPortal(CustomerPortal):
    """ This class is used to super already existing dashboard portal to
    change the template"""

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def change_portal(self, **kw):
        """Replaces already existing work flow of portal view to redirect to
        new template with record values and count"""
        partner_id = request.env.user.partner_id.id
        user = request.env.user
        project_no = 0
        sale_order = request.env['sale.order'].sudo()
        purchase_order = request.env['purchase.order'].sudo()
        account_move = request.env['account.move'].sudo()
        project = request.env['project.project'].sudo()
        task = request.env['project.task'].sudo()
        config_parameters = request.env['ir.config_parameter'].sudo()
        number_project, projects_limited = "", ""
        tasks_limited, number_account = "", ""
        show_project = request.env['ir.config_parameter'
        ].sudo().get_param('portal_dashboard.is_show_project')
        show_account = request.env['ir.config_parameter'].sudo().get_param(
            'portal_dashboard.is_show_recent_invoice_bill')
        show_so_q = (request.env['ir.config_parameter'].sudo().
                     get_param('portal_dashboard.is_show_recent_so_q'))
        show_po_rfq = request.env['ir.config_parameter'
        ].sudo().get_param('portal_dashboard.is_show_recent_po_rfq')
        number_so, sale_orders_limited, quotations_limited = "", "", ""
        number_po, purchase_orders_limited = "", ""
        rfq_limited, invoices_limited = "", ""
        if request.env.ref('base.group_user') in user.groups_id:
            if show_so_q:
                number_so = request.env[
                    'ir.config_parameter'
                ].sudo().get_param('portal_dashboard.sale_count', 0)
                sale_orders_limited = sale_order.search([
                    ('create_uid', '=', user.id),
                    ('state', 'not in', ['draft', 'sent'])
                ], limit=int(number_so))
                quotations_limited = sale_order.search([
                    ('create_uid', '=', user.id),
                    ('state', 'in', ['sent'])
                ], limit=int(number_so))
            if show_po_rfq:
                number_po = config_parameters.get_param(
                    'portal_dashboard.purchase_count', 0)
                purchase_orders_limited = purchase_order.search([
                    ('user_id', '=', user.id),
                    ('state', 'not in', ['draft', 'sent', 'to approve'])
                ], limit=int(number_po))
                rfq_limited = purchase_order.search([
                    ('user_id', '=', user.id),
                    ('state', 'in', ['draft', 'sent', 'to approve'])
                ], limit=int(number_po))
            if show_project:
                number_project = config_parameters.get_param(
                    'portal_dashboard.project_count', 0)
                projects_limited = project.search(
                    ['|', ('user_id', '=', user.id),
                     ('partner_id', '=', partner_id)],
                    limit=int(number_project))
                tasks_limited = task.search(
                    ['|', ('user_id', '=', user.id),
                     ('partner_id', '=', partner_id)],
                    limit=int(number_project))
            if show_account:
                number_account = config_parameters.get_param(
                    'portal_dashboard.account_count', 0)
                invoices_limited = account_move.search([
                    ('invoice_user_id', '=', user.id),
                    ('state', 'not in', ['draft', 'cancel'])
                ], limit=int(number_account))
            sale_orders = sale_order.search([
                ('user_id', '=', user.id),
                ('state', 'not in', ['draft', 'sent'])])
            quotations = sale_order.search([
                ('user_id', '=', user.id),
                ('state', '=', 'sent')])
            purchase_orders = purchase_order.search([('user_id', '=', user.id),
                ('state', 'in', ['purchase'])])
            rfq = purchase_order.search([
                ('user_id', '=', user.id),
                ('state', 'in', ['sent', 'to approve'])])
            project_no = project.search([])
            tasks = task.search([])
            invoices = account_move.search_count(
                self._get_invoices_domain())
        else:
            if show_so_q:
                number_so = config_parameters.get_param(
                    'portal_dashboard.sale_count', 0)
                sale_orders_limited = sale_order.search([
                    ('partner_id', '=', partner_id),
                    ('state', 'not in', ['draft', 'sent'])
                ], limit=int(number_so))
                quotations_limited = sale_order.search([
                    ('partner_id', '=', partner_id),
                    ('state', 'in', ['sent'])
                ], limit=int(number_so))
            if show_po_rfq:
                number_po = config_parameters.get_param(
                    'portal_dashboard.purchase_count', 0)
                purchase_orders_limited = purchase_order.search([
                    ('partner_id', '=', partner_id),
                    ('state', 'not in', ['draft', 'sent', 'to approve'])
                ], limit=int(number_po))
                rfq_limited = purchase_order.search([
                    ('partner_id', '=', partner_id),
                    ('state', 'in', ['draft', 'sent', 'to approve'])
                ], limit=int(number_po))
            if show_project:
                number_project = config_parameters.get_param(
                    'portal_dashboard.project_count', 0)
                projects_limited = project.search(
                    ['|', ('user_id', '=', user.id),
                     ('partner_id', '=', partner_id)],
                    limit=int(number_project))
                tasks_limited = task.search(
                    ['|', ('user_id', '=', user.id),
                     ('partner_id', '=', partner_id)],
                    limit=int(number_project))
            if show_account:
                number_account = config_parameters.get_param(
                    'portal_dashboard.account_count', 0)
                invoices_limited = account_move.search([
                    ('partner_id', '=', partner_id),
                    ('state', 'not in', ['draft', 'cancel'])
                ], limit=int(number_account))
            sale_orders = sale_order.search([
                ('partner_id', '=', partner_id),
                ('state', 'not in', ['draft', 'sent'])])
            quotations = sale_order.search([
                ('user_id', '=', user.id),
                ('state', '=', 'sent')])
            purchase_orders = purchase_order.search([
                ('partner_id', '=', partner_id),
                ('state', '=', 'purchase')])
            rfq = purchase_order.search([
                ('partner_id', '=', partner_id),
                ('state', 'in', ['sent', 'to approve'])])
            projects = project.search([
                ('partner_id', '=', partner_id)])
            for project in projects:
                if (project.privacy_visibility == 'portal' and user.id
                        in project.allowed_portal_user_ids.mapped('id')):
                    project_no += 1
            tasks = task.search([('partner_id', '=', user.partner_id.id)])
            invoices = account_move.search([
                ('partner_id', '=', partner_id),
                ('state', 'not in', ['draft', 'cancel'])])
        values = self._prepare_portal_layout_values()
        values = {'sales_user': values['sales_user'],
                  'page_name': values['page_name'],
                  'sale_order_portal': sale_orders,
                  'quotation_portal': quotations,
                  'purchase_orders_portal': purchase_orders,
                  'rfq_portal': rfq,
                  'projects_portal': project_no,
                  'tasks_portal': tasks,
                  'invoices_portal': invoices,
                  'number_so_portal': number_so,
                  'number_po_portal': number_po,
                  'number_account_portal': number_account,
                  'number_project_portal': number_project,
                  'sale_orders_limited': sale_orders_limited,
                  'quotations_limited': quotations_limited,
                  'purchase_orders_limited': purchase_orders_limited,
                  'rfq_limited': rfq_limited,
                  'invoices_limited': invoices_limited,
                  'projects_limited': projects_limited,
                  'tasks_limited': tasks_limited,
                  'show_so_q': show_so_q,
                  'show_po_rfq': show_po_rfq,
                  'show_project': show_project,
                  'show_account': show_account}
        return request.render("portal_dashboard.replace_dashboard_portal_view",
                              values)
