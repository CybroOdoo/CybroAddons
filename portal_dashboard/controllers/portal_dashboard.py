# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Henna Mehjabin (odoo@cybrosys.com)
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
from odoo import fields
from odoo.fields import Domain
from odoo.http import request, route

from odoo.addons.account.controllers.portal import PortalAccount


class DashboardPortal(PortalAccount):
    """Customer portal dashboard controller rendering KPI cards, recent activity, and analytics."""

    def _get_invoices_domain(self, m_type=None):
        domain = super()._get_invoices_domain(m_type=m_type)
        user = request.env.user
        partner = user.partner_id
        if user.has_group('base.group_user'):
            commercial_partner = partner.commercial_partner_id.id
            internal_partner_domain = ('partner_id', 'child_of', [commercial_partner])
            company_domain = [('company_id', '=', request.env.company.id)] if request.env.company else []
            if m_type == 'out':
                staff_domain = Domain(company_domain + [
                    '|', internal_partner_domain, ('invoice_user_id', '=', user.id),
                ])
            elif m_type == 'in':
                staff_domain = Domain(company_domain + [
                    internal_partner_domain,
                ])
            else:
                staff_domain = Domain(company_domain + [
                    '|',
                    '&', ('move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt']),
                         '|', internal_partner_domain, ('invoice_user_id', '=', user.id),
                    '&', ('move_type', 'in', ['in_invoice', 'in_refund', 'in_receipt']),
                         internal_partner_domain,
                ])
            return Domain(domain) & staff_domain
        return domain

    def _get_overdue_invoices_domain(self, partner_id=None):
        user = request.env.user
        if user.has_group('base.group_user') and not partner_id:
            commercial_partner = user.partner_id.commercial_partner_id.id
            internal_partner_domain = ('partner_id', 'child_of', [commercial_partner])
            company_domain = [('company_id', '=', request.env.company.id)] if request.env.company else []
            return company_domain + [
                ('state', 'not in', ('cancel', 'draft')),
                ('move_type', 'in', ('out_invoice', 'out_receipt')),
                ('payment_state', 'not in', ('in_payment', 'paid', 'reversed', 'blocked', 'invoicing_legacy')),
                ('invoice_date_due', '<', fields.Date.today()),
                '|',
                internal_partner_domain,
                ('invoice_user_id', '=', user.id),
            ]
        return super()._get_overdue_invoices_domain(partner_id=partner_id)

    @route()
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        return super().portal_my_invoices(
            page=page, date_begin=date_begin, date_end=date_end, sortby=sortby, filterby=filterby, **kw,
        )

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        """Render the custom portal dashboard with metrics and recent records."""
        user = request.env.user
        partner = user.partner_id
        is_internal = user.has_group('base.group_user')
        config = request.env['ir.config_parameter'].sudo()

        show_so_q = config.get_param('portal_dashboard.is_show_recent_so_q', default=False)
        show_po_rfq = config.get_param('portal_dashboard.is_show_recent_po_rfq', default=False)
        show_project = config.get_param('portal_dashboard.is_show_project', default=False)
        show_account = config.get_param(
            'portal_dashboard.is_show_recent_invoice_bill', default=False,
        )

        number_so = int(config.get_param('portal_dashboard.sale_count', default=5) or 5)
        number_po = int(config.get_param('portal_dashboard.purchase_count', default=5) or 5)
        number_project = int(config.get_param('portal_dashboard.project_count', default=5) or 5)
        number_account = int(config.get_param('portal_dashboard.account_count', default=5) or 5)

        SaleOrder = request.env['sale.order'].sudo()
        PurchaseOrder = request.env['purchase.order'].sudo()
        AccountMove = request.env['account.move']
        Project = request.env['project.project']
        Task = request.env['project.task']

        if is_internal:
            commercial_partner = partner.commercial_partner_id.id
            internal_partner_domain = ('partner_id', 'child_of', [commercial_partner])

            # Sales domains for internal salesperson or customer partner
            so_domain = [
                '|', internal_partner_domain,
                ('user_id', '=', user.id),
                ('state', 'in', ['sale', 'done']),
            ]
            quotation_domain = [
                '|', internal_partner_domain,
                ('user_id', '=', user.id),
                ('state', 'in', ['draft', 'sent']),
            ]

            # Purchase domains for internal purchaser or vendor partner
            po_domain = [
                '|', internal_partner_domain,
                ('user_id', '=', user.id),
                ('state', 'in', ['purchase', 'done']),
            ]
            rfq_domain = [
                '|', internal_partner_domain,
                ('user_id', '=', user.id),
                ('state', 'in', ['draft', 'sent', 'to approve']),
            ]

            # Invoice & bill domains matching Customer/Salesperson and Vendor
            company_domain = [('company_id', '=', request.env.company.id)] if request.env.company else []
            invoice_domain = company_domain + [
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', 'not in', ['draft', 'cancel']),
                '|',
                internal_partner_domain,
                ('invoice_user_id', '=', user.id),
            ]
            bill_domain = company_domain + [
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', 'not in', ['draft', 'cancel']),
                internal_partner_domain,
            ]

            # Project and Task domains for internal user
            project_domain = [
                ('is_template', '=', False),
                '|',
                internal_partner_domain,
                ('user_id', '=', user.id),
            ]
            task_domain = [
                ('project_id', '!=', False),
                ('is_template', '=', False),
                '|',
                internal_partner_domain,
                ('user_ids', 'in', [user.id]),
            ]
        else:
            commercial_partner = partner.commercial_partner_id.id
            partner_domain = [('partner_id', 'child_of', [commercial_partner])]

            # Sales domains for portal customer: draft quotations are never shown to portal customers
            so_domain = partner_domain + [('state', 'in', ['sale', 'done'])]
            quotation_domain = partner_domain + [('state', 'in', ['sent', 'cancel'])]

            # Purchase domains for portal vendor: draft RFQs are never shown to portal vendors
            po_domain = partner_domain + [('state', 'in', ['purchase', 'done'])]
            rfq_domain = partner_domain + [('state', 'in', ['sent', 'to approve'])]

            # Invoices and vendor bills for portal partner
            company_domain = [('company_id', '=', request.env.company.id)] if request.env.company else []
            invoice_domain = company_domain + partner_domain + [
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', 'not in', ['draft', 'cancel']),
            ]
            bill_domain = company_domain + partner_domain + [
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', 'not in', ['draft', 'cancel']),
            ]

            # Projects & Tasks adhere strictly to core Odoo portal access rules
            project_domain = [('is_template', '=', False)]
            task_domain = [('project_id', '!=', False), ('is_template', '=', False)]

        # Efficient record counts via search_count
        count_so = SaleOrder.search_count(so_domain)
        count_quotation = SaleOrder.search_count(quotation_domain)
        count_po = PurchaseOrder.search_count(po_domain)
        count_rfq = PurchaseOrder.search_count(rfq_domain)
        count_invoice = AccountMove.search_count(invoice_domain) if AccountMove.has_access('read') else 0
        count_bill = AccountMove.search_count(bill_domain) if AccountMove.has_access('read') else 0
        count_project = Project.search_count(project_domain) if Project.has_access('read') else 0
        count_task = Task.search_count(task_domain) if Task.has_access('read') else 0

        # Query only the limited recent records required for displayed tables
        sale_orders_limited = (
            SaleOrder.search(so_domain, order='date_order desc', limit=number_so)
            if show_so_q else SaleOrder.browse()
        )
        quotations_limited = (
            SaleOrder.search(quotation_domain, order='date_order desc', limit=number_so)
            if show_so_q else SaleOrder.browse()
        )
        purchase_orders_limited = (
            PurchaseOrder.search(po_domain, order='date_approve desc, date_order desc', limit=number_po)
            if show_po_rfq else PurchaseOrder.browse()
        )
        rfq_limited = (
            PurchaseOrder.search(rfq_domain, order='date_order desc', limit=number_po)
            if show_po_rfq else PurchaseOrder.browse()
        )
        invoices_limited = (
            AccountMove.search(invoice_domain, order='invoice_date desc', limit=number_account)
            if (show_account and AccountMove.has_access('read')) else AccountMove.browse()
        )
        bills_limited = (
            AccountMove.search(bill_domain, order='invoice_date desc', limit=number_account)
            if (show_account and AccountMove.has_access('read')) else AccountMove.browse()
        )
        projects_limited = (
            Project.search(project_domain, order='create_date desc', limit=number_project)
            if (show_project and Project.has_access('read')) else Project.browse()
        )
        tasks_limited = (
            Task.search(task_domain, order='create_date desc', limit=number_project)
            if (show_project and Task.has_access('read')) else Task.browse()
        )

        values = self._prepare_portal_layout_values()
        values.update({
            'count_quotation': count_quotation,
            'count_so': count_so,
            'count_po': count_po,
            'count_rfq': count_rfq,
            'count_invoice': count_invoice,
            'count_bill': count_bill,
            'count_project': count_project,
            'count_task': count_task,

            'quotations_limited': quotations_limited,
            'sale_orders_limited': sale_orders_limited,
            'purchase_orders_limited': purchase_orders_limited,
            'rfq_limited': rfq_limited,
            'invoices_limited': invoices_limited,
            'bills_limited': bills_limited,
            'projects_limited': projects_limited,
            'tasks_limited': tasks_limited,

            'number_so_portal': number_so,
            'number_po_portal': number_po,
            'number_account_portal': number_account,
            'number_project_portal': number_project,

            'show_so_q': bool(show_so_q),
            'show_po_rfq': bool(show_po_rfq),
            'show_project': bool(show_project),
            'show_account': bool(show_account),
        })
        return request.render("portal_dashboard.replace_dashboard_portal_view", values)
