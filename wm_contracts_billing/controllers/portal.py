# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
import base64
from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class WmPortalController(CustomerPortal):
    """Extends Customer Portal with waste management contracts and service subscription views."""

    def _prepare_portal_layout_values(self):
        """
        Prepare values for the main portal layout page, including counts of
        contracts, collection orders, and subscriptions.
        """
        values = super()._prepare_portal_layout_values()
        partner = request.env.user.partner_id

        has_collection = 'wm.collection.order' in request.env
        has_customer = 'wm.partner.contract' in request.env
        has_subscription = 'wm.subscription' in request.env

        values['has_collection_module'] = has_collection
        values['has_customer_module'] = has_customer
        values['has_subscription_module'] = has_subscription

        if has_collection:
            values['collection_order_count'] = request.env['wm.collection.order'].sudo().search_count([
                ('partner_id', '=', partner.id)
            ])
        if has_customer:
            values['contract_count'] = request.env['wm.partner.contract'].sudo().search_count([
                ('partner_id', '=', partner.id)
            ])
        if has_subscription:
            values['subscription_count'] = request.env['wm.subscription'].sudo().search_count([
                ('partner_id', '=', partner.id)
            ])

        return values

    @http.route(['/my/collection/orders', '/my/collection/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_collection_orders(self, page=1, **kw):
        """
        Render the collection orders list page with pagination.
        """
        if 'wm.collection.order' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        Order = request.env['wm.collection.order'].sudo()
        domain = [('partner_id', '=', partner.id)]

        orders_count = Order.search_count(domain)
        pager = request.website.pager(
            url="/my/collection/orders",
            total=orders_count,
            page=page,
            step=10
        )

        orders = Order.search(domain, order='create_date desc', limit=10, offset=pager['offset'])

        return request.render('wm_contracts_billing.portal_my_collection_orders', {
            'orders': orders,
            'page_name': 'collection_order',
            'pager': pager,
            'default_url': '/my/collection/orders',
        })

    @http.route(['/my/collection/orders/<int:order_id>'], type='http', auth="user", website=True)
    def portal_my_collection_order_detail(self, order_id, **kw):
        """
        Render the detail view page for a specific collection order.
        """
        if 'wm.collection.order' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        order = request.env['wm.collection.order'].sudo().browse(order_id).exists()
        if not order or order.partner_id != partner:
            return request.not_found()

        return request.render('wm_contracts_billing.portal_my_collection_order_detail', {
            'order': order,
            'page_name': 'collection_order',
        })

    @http.route(['/my/collection/orders/<int:order_id>/pdf'], type='http', auth="user", website=True)
    def portal_my_collection_order_pdf(self, order_id, **kw):
        """
        Download the PDF report of a specific collection order.
        """
        if 'wm.collection.order' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        order = request.env['wm.collection.order'].sudo().browse(order_id).exists()
        if not order or order.partner_id != partner:
            return request.not_found()

        pdf, _unused = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'wm_collection.collection_order_report', [order.id]
        )
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename="%s.pdf"' % order.name)
        ]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        download_token = kw.get('downloadToken')
        if download_token:
            response.set_cookie('fileDownloadToken', download_token, max_age=30)
        return response

    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_contracts(self, page=1, **kw):
        """
        Serve the portal-facing waste management contracts list view, filtering
        contracts by the logged-in partner and applying date/state filters from
        query parameters.
        """
        if 'wm.partner.contract' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        Contract = request.env['wm.partner.contract'].sudo()
        domain = [('partner_id', '=', partner.id)]

        contracts_count = Contract.search_count(domain)
        pager = request.website.pager(
            url="/my/contracts",
            total=contracts_count,
            page=page,
            step=10
        )

        contracts = Contract.search(domain, order='create_date desc', limit=10, offset=pager['offset'])

        return request.render('wm_contracts_billing.portal_my_contracts', {
            'contracts': contracts,
            'page_name': 'contract',
            'pager': pager,
            'default_url': '/my/contracts',
        })

    @http.route(['/my/contracts/<int:contract_id>'], type='http', auth="user", website=True)
    def portal_my_contract_detail(self, contract_id, **kw):
        """
        Render the detail view page for a specific contract.
        """
        if 'wm.partner.contract' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        contract = request.env['wm.partner.contract'].sudo().browse(contract_id).exists()
        if not contract or contract.partner_id != partner:
            return request.not_found()

        sign_url = False
        if contract.state in ('draft', 'sent') and hasattr(contract, 'get_portal_signature_url'):
            sign_url = contract.get_portal_signature_url()

        return request.render('wm_contracts_billing.portal_my_contract_detail', {
            'contract': contract,
            'page_name': 'contract',
            'sign_url': sign_url,
        })

    @http.route(['/my/contracts/<int:contract_id>/pdf'], type='http', auth="user", website=True)
    def portal_my_contract_pdf(self, contract_id, **kw):
        """
        Download the PDF report of a specific contract (signed version if
        available).
        """
        if 'wm.partner.contract' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        contract = request.env['wm.partner.contract'].sudo().browse(contract_id).exists()
        if not contract or contract.partner_id != partner:
            return request.not_found()

        pdf = False
        if 'wm.signature.request' in request.env:
            sig_request = request.env['wm.signature.request'].sudo().search([
                ('reference_doc', '=', f'wm.partner.contract,{contract.id}'),
                ('signed_document', '!=', False),
            ], order='id desc', limit=1)
            if sig_request and sig_request.signed_document:
                pdf = base64.b64decode(sig_request.signed_document)

        if not pdf:
            pdf, _unused = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'wm_contracts_billing.partner_contract_report', [contract.id]
            )
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename="%s.pdf"' % contract.name)
        ]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        download_token = kw.get('downloadToken')
        if download_token:
            response.set_cookie('fileDownloadToken', download_token, max_age=30)
        return response

    @http.route(['/my/contracts/<int:contract_id>/cancel'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_cancel_contract(self, contract_id, cancel_reason=None, **kw):
        """
        Customer self-service contract cancellation from portal.
        """
        if 'wm.partner.contract' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        contract = request.env['wm.partner.contract'].sudo().browse(contract_id).exists()
        if not contract or contract.partner_id != partner:
            return request.not_found()

        if contract.state in ('draft', 'sent', 'signed', 'confirmed', 'ongoing'):
            reason_msg = cancel_reason or _('Cancelled by customer via Website Portal')
            contract.action_cancel()
            contract.message_post(body=_("Contract cancelled by customer via portal. Reason: %s") % reason_msg)
        return request.redirect('/my/contracts/%s?success=cancelled' % contract.id)

    @http.route(['/my/collection/orders/<int:order_id>/cancel'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_cancel_collection_order(self, order_id, cancel_reason=None, **kw):
        """
        Customer self-service collection order cancellation from portal.
        """
        if 'wm.collection.order' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        order = request.env['wm.collection.order'].sudo().browse(order_id).exists()
        if not order or order.partner_id != partner:
            return request.not_found()

        if order.state in ('draft', 'scheduled', 'dispatched'):
            reason_msg = cancel_reason or _('Cancelled by customer via Website Portal')
            order.action_cancel()
            order.message_post(body=_("Collection order cancelled by customer via portal. Reason: %s") % reason_msg)
        return request.redirect('/my/collection/orders/%s?success=cancelled' % order.id)

    @http.route(['/my/subscriptions', '/my/subscriptions/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_subscriptions(self, page=1, **kw):
        """
        Render the customer subscriptions list page with active subscriptions
        prioritized on top.
        """
        if 'wm.subscription' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        Subscription = request.env['wm.subscription'].sudo()
        domain = [('partner_id', '=', partner.id)]

        all_subscriptions = Subscription.search(domain)
        sorted_subscriptions = all_subscriptions.sorted(
            key=lambda s: (0 if s.state == 'active' else 1, -(s.id or 0))
        )

        subscriptions_count = len(sorted_subscriptions)
        pager = request.website.pager(
            url="/my/subscriptions",
            total=subscriptions_count,
            page=page,
            step=10
        )

        offset = pager['offset']
        subscriptions = sorted_subscriptions[offset:offset + 10]

        return request.render('wm_contracts_billing.portal_my_subscriptions', {
            'subscriptions': subscriptions,
            'page_name': 'subscription',
            'pager': pager,
            'default_url': '/my/subscriptions',
        })

    @http.route(['/my/subscriptions/<int:subscription_id>'], type='http', auth="user", website=True)
    def portal_my_subscription_detail(self, subscription_id, **kw):
        """
        Render the detail view page for a specific subscription.
        """
        if 'wm.subscription' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        subscription = request.env['wm.subscription'].sudo().browse(subscription_id).exists()
        if not subscription or subscription.partner_id != partner:
            return request.not_found()

        return request.render('wm_contracts_billing.portal_my_subscription_detail', {
            'subscription': subscription,
            'page_name': 'subscription',
        })

    @http.route(['/my/subscriptions/<int:subscription_id>/pdf'], type='http', auth="user", website=True)
    def portal_my_subscription_pdf(self, subscription_id, **kw):
        """
        Download the PDF report of a specific subscription.
        """
        if 'wm.subscription' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        subscription = request.env['wm.subscription'].sudo().browse(subscription_id).exists()
        if not subscription or subscription.partner_id != partner:
            return request.not_found()

        pdf, _unused = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'wm_subscription.report_subscription_document', [subscription.id]
        )
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'attachment; filename="%s.pdf"' % subscription.name)
        ]
        response = request.make_response(pdf, headers=pdfhttpheaders)
        download_token = kw.get('downloadToken')
        if download_token:
            response.set_cookie('fileDownloadToken', download_token, max_age=30)
        return response

    @http.route(['/my/subscriptions/<int:subscription_id>/cancel'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_cancel_subscription(self, subscription_id, cancel_reason=None, **kw):
        """
        Customer self-service subscription cancellation from portal.
        """
        if 'wm.subscription' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        subscription = request.env['wm.subscription'].sudo().browse(subscription_id).exists()
        if not subscription or subscription.partner_id != partner:
            return request.not_found()

        if subscription.state in ['active', 'draft', 'paused']:
            subscription.action_cancel(reason=cancel_reason or 'Cancelled by customer via Website Portal')
        return request.redirect('/my/subscriptions/%s?success=cancelled' % subscription.id)

    @http.route(['/my/subscriptions/new'], type='http', auth="user", website=True)
    def portal_create_subscription(self, **kw):
        """
        Handle the portal contract subscription form submission, validate the
        incoming parameters, and create a new contract or service request
        record on behalf of the portal user.
        """
        if 'wm.subscription' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        plans = request.env['wm.subscription.plan'].sudo().search([('active', '=', True)])

        collection_points = []
        if 'wm.collection.point' in request.env:
            active_subs = request.env['wm.subscription'].sudo().search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'active'),
            ])
            active_point_ids = active_subs.mapped('collection_point_id').ids
            collection_points = request.env['wm.collection.point'].sudo().search([
                ('partner_id', '=', partner.id),
                ('id', 'not in', active_point_ids)
            ])

        today_date = date.today().strftime('%Y-%m-%d')

        return request.render('wm_contracts_billing.portal_create_subscription_template', {
            'partner': partner,
            'plans': plans,
            'collection_points': collection_points,
            'today_date': today_date,
            'error': kw.get('error'),
            'is_sub_request_page': True,
            'page_name': 'subscription',
        })

    @http.route(['/my/subscriptions/submit'], type='http', auth="user", methods=['POST'], website=True, csrf=True)
    def portal_submit_subscription(self, plan_id=None, collection_point_id=None, start_date=None, end_date=None, auto_renew=None, **post):
        """
        Process subscription creation submission from portal.
        """
        if 'wm.subscription' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id

        if not plan_id or not collection_point_id or not start_date or not end_date:
            return request.redirect('/my/subscriptions/new?error=missing_fields')

        try:
            start_d = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_d = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return request.redirect('/my/subscriptions/new?error=missing_fields')

        if end_d <= start_d:
            return request.redirect('/my/subscriptions/new?error=invalid_dates')

        try:
            plan_id_int = int(plan_id)
            point_id_int = int(collection_point_id)
        except (ValueError, TypeError):
            return request.redirect('/my/subscriptions/new?error=missing_fields')

        plan = request.env['wm.subscription.plan'].sudo().browse(plan_id_int).exists()
        if not plan or not plan.active:
            return request.redirect('/my/subscriptions/new?error=invalid_plan')

        point = request.env['wm.collection.point'].sudo().browse(point_id_int).exists() if 'wm.collection.point' in request.env else False
        if not point or point.partner_id != partner:
            return request.redirect('/my/subscriptions/new?error=invalid_point')

        active_sub_count = request.env['wm.subscription'].sudo().search_count([
            ('collection_point_id', '=', point.id),
            ('state', '=', 'active'),
        ])
        if active_sub_count:
            return request.redirect('/my/subscriptions/new?error=active_point_subscription')

        sub_vals = {
            'partner_id': partner.id,
            'plan_id': plan.id,
            'collection_point_id': point.id,
            'start_date': start_date,
            'end_date': end_date,
            'price': plan.price,
            'auto_renew': bool(auto_renew),
            'state': 'draft',
        }
        subscription = request.env['wm.subscription'].sudo().create(sub_vals)

        return request.redirect('/my/subscriptions/%s?success=created' % subscription.id)

    @http.route(['/my/collection/dashboard'], type='http', auth="user", website=True)
    def portal_my_collection_dashboard(self, date_start=None, date_end=None, preset='last_90',
                                       period_year=None, period_month=None, period_quarter=None,
                                       **kw):
        """
        Render the collection metrics and KPI dashboard page.
        """
        if 'wm.collection.order' not in request.env:
            return request.not_found()
        partner = request.env.user.partner_id
        today = date.today()
        _month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                        'July', 'August', 'September', 'October', 'November', 'December']
        all_time = False

        if preset == 'today':
            start_dt, end_dt = today, today
        elif preset == 'yesterday':
            start_dt, end_dt = today - timedelta(days=1), today - timedelta(days=1)
        elif preset == 'last_7':
            start_dt, end_dt = today - timedelta(days=6), today
        elif preset == 'last_30':
            start_dt, end_dt = today - timedelta(days=29), today
        elif preset == 'last_90':
            start_dt, end_dt = today - timedelta(days=89), today
        elif preset == 'month_to_date':
            start_dt, end_dt = today.replace(day=1), today
        elif preset == 'last_month':
            last_m = today.replace(day=1) - timedelta(days=1)
            start_dt, end_dt = last_m.replace(day=1), last_m
        elif preset == 'month':
            year = int(period_year) if period_year else today.year
            month = int(period_month) if period_month else today.month
            period_year, period_month = year, month
            start_dt = date(year, month, 1)
            end_dt = (start_dt + relativedelta(months=1)) - timedelta(days=1)
        elif preset == 'quarter':
            year = int(period_year) if period_year else today.year
            q = int(period_quarter) if period_quarter else (today.month - 1) // 3 + 1
            period_year, period_quarter = year, q
            start_dt = date(year, (q - 1) * 3 + 1, 1)
            end_dt = (start_dt + relativedelta(months=3)) - timedelta(days=1)
        elif preset == 'ytd':
            start_dt, end_dt = date(today.year, 1, 1), today
        elif preset == 'last_12':
            start_dt, end_dt = today - relativedelta(months=12) + timedelta(days=1), today
        elif preset == 'year':
            year = int(period_year) if period_year else today.year
            period_year = year
            start_dt, end_dt = date(year, 1, 1), date(year, 12, 31)
        elif preset == 'all_time':
            all_time = True
            start_dt, end_dt = date(2000, 1, 1), today
        else:
            try:
                start_dt = datetime.strptime(date_start, '%Y-%m-%d').date() if date_start else today - timedelta(days=89)
                end_dt = datetime.strptime(date_end, '%Y-%m-%d').date() if date_end else today
                if start_dt > end_dt:
                    start_dt, end_dt = end_dt, start_dt
            except (ValueError, TypeError):
                start_dt, end_dt = today - timedelta(days=89), today
            preset = 'custom'

        # ── Human-readable label ──────────────────────────────────────────
        _simple_labels = {
            'today': 'Today', 'yesterday': 'Yesterday',
            'last_7': 'Last 7 Days', 'last_30': 'Last 30 Days', 'last_90': 'Last 90 Days',
            'month_to_date': 'Month to Date', 'last_month': 'Last Month',
            'ytd': 'Year to Date', 'last_12': 'Last 12 Months', 'all_time': 'All time',
        }
        if preset in _simple_labels:
            range_label = _simple_labels[preset]
        elif preset == 'month':
            range_label = '%s %d' % (_month_names[(period_month or today.month) - 1], period_year or today.year)
        elif preset == 'quarter':
            range_label = 'Q%d %d' % (period_quarter or 1, period_year or today.year)
        elif preset == 'year':
            range_label = str(period_year or today.year)
        elif preset == 'custom':
            if start_dt == end_dt:
                range_label = start_dt.strftime('%b %d, %Y')
            elif start_dt.year == end_dt.year:
                range_label = '%s – %s' % (start_dt.strftime('%b %d'), end_dt.strftime('%b %d, %Y'))
            else:
                range_label = '%s – %s' % (start_dt.strftime('%b %d, %Y'), end_dt.strftime('%b %d, %Y'))
        else:
            range_label = '%s – %s' % (start_dt.strftime('%b %d, %Y'), end_dt.strftime('%b %d, %Y'))

        # ── Global prev / next (arrows beside the button) ─────────────────
        delta = (end_dt - start_dt).days + 1
        if preset in ('month', 'last_month'):
            prev_start = start_dt - relativedelta(months=1)
            next_start = start_dt + relativedelta(months=1)
        elif preset == 'quarter':
            prev_start = start_dt - relativedelta(months=3)
            next_start = start_dt + relativedelta(months=3)
        elif preset == 'year':
            prev_start = start_dt - relativedelta(years=1)
            next_start = start_dt + relativedelta(years=1)
        else:
            prev_start = start_dt - timedelta(days=delta)
            next_start = start_dt + timedelta(days=delta)
        prev_end = prev_start + timedelta(days=delta - 1)
        next_end = next_start + timedelta(days=delta - 1)
        has_next = next_start <= today

        # ── Per-period dropdown row navigation ───────────────────────────
        # Month
        cur_m_y = int(period_year) if preset == 'month' and period_year else today.year
        cur_m_m = int(period_month) if preset == 'month' and period_month else today.month
        prev_m = date(cur_m_y, cur_m_m, 1) - relativedelta(months=1)
        next_m = date(cur_m_y, cur_m_m, 1) + relativedelta(months=1)
        month_label = '%s %d' % (_month_names[cur_m_m - 1], cur_m_y)
        month_prev_url = '/my/collection/dashboard?preset=month&period_year=%d&period_month=%d' % (prev_m.year, prev_m.month)
        month_next_url = '/my/collection/dashboard?preset=month&period_year=%d&period_month=%d' % (next_m.year, next_m.month)
        month_has_next = next_m <= today
        # Quarter
        cur_q_y = int(period_year) if preset == 'quarter' and period_year else today.year
        cur_q_q = int(period_quarter) if preset == 'quarter' and period_quarter else (today.month - 1) // 3 + 1
        prev_q_start = date(cur_q_y, (cur_q_q - 1) * 3 + 1, 1) - relativedelta(months=3)
        next_q_start = date(cur_q_y, (cur_q_q - 1) * 3 + 1, 1) + relativedelta(months=3)
        quarter_label = 'Q%d %d' % (cur_q_q, cur_q_y)
        quarter_prev_url = '/my/collection/dashboard?preset=quarter&period_year=%d&period_quarter=%d' % (
            prev_q_start.year, (prev_q_start.month - 1) // 3 + 1)
        quarter_next_url = '/my/collection/dashboard?preset=quarter&period_year=%d&period_quarter=%d' % (
            next_q_start.year, (next_q_start.month - 1) // 3 + 1)
        quarter_has_next = next_q_start <= today
        # Year
        cur_year_val = int(period_year) if preset == 'year' and period_year else today.year
        year_label = str(cur_year_val)
        year_prev_url = '/my/collection/dashboard?preset=year&period_year=%d' % (cur_year_val - 1)
        year_next_url = '/my/collection/dashboard?preset=year&period_year=%d' % (cur_year_val + 1)
        year_has_next = cur_year_val < today.year

        # ── Domain ───────────────────────────────────────────────────────
        domain = [('partner_id', '=', partner.id)]
        if not all_time:
            domain += [
                ('create_date', '>=', start_dt.strftime('%Y-%m-%d')),
                ('create_date', '<=', end_dt.strftime('%Y-%m-%d 23:59:59')),
            ]
        orders = request.env['wm.collection.order'].sudo().search(domain, order='create_date desc')

        # ── KPI Calculations ─────────────────────────────────────────────
        total_collections = len(orders)
        completed_orders = orders.filtered(lambda o: o.state in ['completed', 'signed', 'invoiced'])
        total_completed = len(completed_orders)
        total_weight = sum(completed_orders.mapped('confirmed_weight'))
        avg_weight = total_weight / total_completed if total_completed > 0 else 0.0
        total_spent = sum(completed_orders.mapped('order_line_ids').mapped('total_amount'))

        category_data = {}
        for line in completed_orders.mapped('order_line_ids'):
            cat = getattr(line, 'category_id', False) or (line.product_id.wm_waste_category_id if line.product_id else False)
            if cat:
                c_id = cat.id
                category_data.setdefault(c_id, {'name': cat.name, 'weight': 0.0, 'amount': 0.0})
                category_data[c_id]['weight'] += line.weight
                category_data[c_id]['amount'] += line.total_amount
            elif line.product_id:
                p_id = f"prod_{line.product_id.id}"
                category_data.setdefault(p_id, {'name': line.product_id.name, 'weight': 0.0, 'amount': 0.0})
                category_data[p_id]['weight'] += line.weight
                category_data[p_id]['amount'] += line.total_amount

        category_list = sorted(category_data.values(), key=lambda x: x['weight'], reverse=True)
        for cat in category_list:
            cat['percentage'] = round((cat['weight'] / total_weight) * 100, 1) if total_weight else 0.0

        point_data = {}
        for order in completed_orders:
            if order.collection_point_id:
                p_id = order.collection_point_id.id
                point_data.setdefault(p_id, {'name': order.collection_point_id.name, 'orders_count': 0, 'weight': 0.0})
                point_data[p_id]['orders_count'] += 1
                point_data[p_id]['weight'] += order.confirmed_weight
        point_list = sorted(point_data.values(), key=lambda x: x['weight'], reverse=True)

        status_counts = {
            'draft': 0, 'dispatched': 0, 'in_progress': 0,
            'completed': 0, 'signed': 0, 'invoiced': 0, 'missed': 0,
        }
        for o in orders:
            if o.state in status_counts:
                status_counts[o.state] += 1

        return request.render('wm_contracts_billing.portal_collection_dashboard', {
            'page_name': 'collection_dashboard',
            'orders': orders[:10],
            'total_collections': total_collections,
            'total_completed': total_completed,
            'total_weight': round(total_weight, 2),
            'avg_weight': round(avg_weight, 2),
            'total_spent': round(total_spent, 2),
            'categories': category_list,
            'collection_points': point_list,
            'status_counts': status_counts,
            'date_start': start_dt.strftime('%Y-%m-%d'),
            'date_end': end_dt.strftime('%Y-%m-%d'),
            'range_label': range_label,
            'current_preset': preset,
            # Global prev/next arrows
            'prev_date_start': prev_start.strftime('%Y-%m-%d'),
            'prev_date_end': prev_end.strftime('%Y-%m-%d'),
            'next_date_start': next_start.strftime('%Y-%m-%d'),
            'next_date_end': next_end.strftime('%Y-%m-%d'),
            'has_next': has_next,
            # Dropdown period rows
            'month_label': month_label,
            'month_prev_url': month_prev_url,
            'month_next_url': month_next_url,
            'month_has_next': month_has_next,
            'quarter_label': quarter_label,
            'quarter_prev_url': quarter_prev_url,
            'quarter_next_url': quarter_next_url,
            'quarter_has_next': quarter_has_next,
            'year_label': year_label,
            'year_prev_url': year_prev_url,
            'year_next_url': year_next_url,
            'year_has_next': year_has_next,
        })
