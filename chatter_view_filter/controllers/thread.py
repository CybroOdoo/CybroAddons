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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.mail.tools.discuss import Store

class ThreadController(http.Controller):
    @http.route("/mail/thread/messages", methods=["POST"], type="json",
                auth="user")
    def mail_thread_messages(self, thread_model, thread_id, search_term=None,
                             before=None, after=None, around=None, limit=30,
                             search_date=None, follower_search_id = None):
        """customize the function for adding new arguments"""
        domain = [
            ("res_id", "=", int(thread_id)),
            ("model", "=", thread_model),
            ("message_type", "!=", "user_notification"),
        ]
        res = request.env["mail.message"]._message_fetch(
            domain, search_term=search_term, before=before, after=after,
            around=around, limit=limit, search_date=search_date,
            follower_search_id=follower_search_id)
        if not request.env.user._is_public():
            res["messages"].set_message_done()
            messages = res.pop("messages")
        return {**res,
                "data": Store(messages, for_current_user=True).get_result(),
                "messages": Store.many_ids(messages)}
