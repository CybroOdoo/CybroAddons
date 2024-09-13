# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
#############################################################################
"""Franchise portal controller"""
import binascii
from odoo import fields, http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError
from odoo.addons.portal.controllers.mail import _message_post_helper


class FranchisePortal(http.Controller):
    """Franchise Portal template."""

    @http.route(['/my/franchise'], type='http', auth="public",
                website=True)
    def display_franchise_registration(self):
        """function to display franchise registrations from backend."""
        franchise_registration = request.env['franchise.dealer'].sudo().search(
            [('state', 'in', ('e_contract', 'f_signed', 'g_declined'))])
        dealer_dict = {'franchise_registration': franchise_registration,
                       'page_name': 'franchise_registrations'}
        return request.render("franchise_management.portal_my_franchise",
                              dealer_dict)

    @http.route(['/my/franchise/<int:franchise_id>'], type='http', auth="public",
                website=True)
    def portal_sign_page(self, franchise_id):
        """Franchise Portal Sign Page."""
        franchise = request.env['franchise.dealer'].sudo().browse(franchise_id)
        return request.render("franchise_management.franchise_portal",
                              {'franchise': franchise,
                               'page_name': 'registration_details'})

    @http.route(['/my/franchise/<int:dealer_id>/decline'], type='http', auth="public",
                methods=['POST'], website=True, csrf=True)
    def portal_franchise_decline(self, dealer_id):
        """Declining the contract sign"""
        order_sudo = request.env['franchise.dealer'].sudo().browse(dealer_id)
        order_sudo.contract_declined()
        return request.redirect(f'my/franchise/{dealer_id}')

    @http.route(['/my/franchise/<int:dealer_id>/accept'], type='json', auth="public",
                website=True, csrf=True)
    def portal_franchise_accept(self, dealer_id, name=None, signature=None,
                                access_token=None):
        """Accepting the contract and signing it."""
        access_token = access_token or request.httprequest.args.get(
            'access_token')
        try:
            order_sudo = request.env['franchise.dealer'].sudo().browse(dealer_id)
        except (AccessError, MissingError):
            return {'error': _('Invalid order.')}
        try:
            order_sudo.write({
                'signed_by': name,
                'signed_on': fields.Datetime.now(),
                'signature': signature,
            })
            request.env.cr.commit()
            order_sudo.contract_signed()
            list_login = request.env['res.users'].sudo().search([]).mapped(
                'login')
            # Check if the dealer's mail is not in the list_login
            if order_sudo.dealer_mail not in list_login:
                order_sudo.create_portal_user()
                order_sudo._send_order_confirmation_mail()
                order_sudo.dealer_portal_user.is_dealer_user = True
            if order_sudo.dealer_mail in list_login:
                franchise_users_id = request.env['res.users'].sudo().search([
                    ('login', '=', order_sudo.dealer_mail)])
                order_sudo.dealer_portal_user = franchise_users_id
        except (TypeError, binascii.Error) as e:
            return {'error': _('Invalid signature data.')}
        signed_pdf = request.env.ref('franchise_management.franchise_contract_report_action').sudo()._render_qweb_pdf(
            [order_sudo.id])[0]
        _message_post_helper(
            'franchise.dealer',
            order_sudo.id,
            _('Order signed by %s', name),
            attachments=[('%s.signed_pdf' % order_sudo.dealer_name,
                          signed_pdf)],
            token=access_token,
        )
        query_string = "&message=sign_ok"
        return {
            'force_refresh': True,
            'redirect_url': order_sudo.get_portal_url(
                query_string=query_string),
        }
