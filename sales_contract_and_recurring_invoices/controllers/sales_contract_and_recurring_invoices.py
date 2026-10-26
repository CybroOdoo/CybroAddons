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
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class CustomerPortalContracts(CustomerPortal):
    """ Customer portal controller for subscription contracts """

    def _prepare_portal_counter_values(self, counter):
        """ Provide counter metadata for the portal home counters system in Odoo 20.0 """
        if counter == 'contract_count':
            user = request.env.user
            domain = []
            if not user.has_group('base.group_system'):
                domain = [('partner_id', 'child_of', [user.commercial_partner_id.id])]
            return 'subscription.contracts', domain, 'read'
        return super()._prepare_portal_counter_values(counter)

    @http.route(['/my/contracts', '/my/contracts/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_contracts(self, page=1, **kw):
        """ Displays Contracts in portal """
        values = self._prepare_portal_layout_values()
        user = request.env.user
        domain = []
        if not user.has_group('base.group_system'):
            domain = [('partner_id', 'child_of', [user.commercial_partner_id.id])]

        contract_obj = request.env['subscription.contracts']
        total_contracts = contract_obj.search_count(domain)
        pager = portal_pager(
            url="/my/contracts",
            total=total_contracts,
            page=page,
            step=self._items_per_page,
        )
        records = contract_obj.search(
            domain,
            limit=self._items_per_page,
            offset=pager['offset'],
        )
        values.update({
            'records': records,
            'page_name': 'contract',
            'pager': pager,
            'default_url': '/my/contracts',
        })
        return request.render(
            'sales_contract_and_recurring_invoices.tmp_contract_details',
            values)

    @http.route(['/contracts/<int:contract_id>', '/contracts/<int:contract_id>/'], type='http', auth='user', website=True)
    def portal_contract_detail(self, contract_id, **kw):
        """ Customer portal subscription contract detail """
        contract = request.env['subscription.contracts'].browse(contract_id)
        if not contract.exists():
            return request.not_found()
        user = request.env.user
        if not user.has_group('base.group_system') and contract.partner_id not in (
            user.partner_id.commercial_partner_id.child_ids | user.partner_id.commercial_partner_id
        ):
            return request.not_found()

        values = {
            'records': contract,
            'page_name': 'contract_detail',
        }
        return request.render(
            'sales_contract_and_recurring_invoices.contract_details', values)

    @http.route('/my/contracts/report/<int:contract_id>', type='http', auth='user', website=True)
    def action_print_report(self, contract_id, **kw):
        """ Download contract report in PDF format """
        contract = request.env['subscription.contracts'].browse(contract_id)
        if not contract.exists():
            return request.not_found()
        user = request.env.user
        if not user.has_group('base.group_system') and contract.partner_id not in (
            user.partner_id.commercial_partner_id.child_ids | user.partner_id.commercial_partner_id
        ):
            return request.not_found()

        report_ref = 'sales_contract_and_recurring_invoices.action_report_subscription_contracts'
        return self._show_report(
            model=contract,
            report_type='pdf',
            report_ref=report_ref,
            download=True,
        )
