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
import os
from odoo.addons.web.controllers.session import Session as WebSession
from odoo import exceptions, http
from odoo.http import request
from odoo.http.session import session_store, logout as odoo_logout


def clear_session_history(u_sid):
    """ Clear all the user session histories of a particular user """
    store = session_store()
    identifier = u_sid[:42] if u_sid else False
    if not identifier or identifier in store.get_missing_session_identifiers(
            [identifier]):
        return False
    store.delete_from_identifiers([identifier])
    return identifier in store.get_missing_session_identifiers([identifier])


def super_clear_all():
    """ Clear all the user session histories """
    store = session_store()
    for root, _dirs, files in os.walk(store.path):
        for fname in files:
            try:
                os.unlink(os.path.join(root, fname))
            except OSError:
                pass
    return True


class Session(WebSession):
    """
    This class includes methods to handle user logouts, clear individual user
    sessions, and perform a force logout, which logs out from all devices.
    """

    @http.route('/web/session/logout', type='http', auth="none", methods=['GET', 'POST'])
    def logout(self, redirect='/web'):
        """ Logs out the current user by clearing their session. """
        if request.session.uid:
            user = request.env['res.users'].sudo().browse(request.session.uid)
            if user.exists():
                user._clear_session()
        odoo_logout(request.session, keep_db=True)
        return request.redirect(redirect, 303)

    @http.route('/clear_all_sessions', type='http', auth="user", methods=['POST'], csrf=True)
    def logout_all(self, redirect='/web', f_uid=False):
        """ Log out from all the sessions of the current user or target user (admin only). """
        target_uid = int(f_uid) if f_uid else request.session.uid
        if target_uid != request.session.uid and not request.env.user.has_group('base.group_system'):
            raise exceptions.AccessDenied()
        user = request.env['res.users'].sudo().browse(target_uid)
        if user.exists():
            if user.sid:
                clear_session_history(user.sid)
            user._clear_session()
        if target_uid == request.session.uid:
            odoo_logout(request.session, keep_db=True)
        return request.redirect(redirect, 303)

    @http.route('/super/logout_all', type='http', auth="user", methods=['POST'], csrf=True)
    def super_logout_all(self, redirect='/web'):
        """ Log out from all the sessions of all users (admin only). """
        if not request.env.user.has_group('base.group_system'):
            raise exceptions.AccessDenied()
        users = request.env['res.users'].sudo().search([])
        for user in users:
            if user.sid:
                clear_session_history(user.sid)
            user._clear_session()
        super_clear_all()
        odoo_logout(request.session, keep_db=True)
        return request.redirect(redirect, 303)
