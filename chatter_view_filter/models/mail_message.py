# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models
from odoo.osv import expression
from datetime import datetime, timedelta


class MailMessage(models.Model):
    """Inherited message model for super the _message_fetch """
    _inherit = 'mail.message'

    def _message_fetch(self, domain, search_term=None, before=None, after=None,
                       around=None, limit=30, search_date=None,
                       follower_search_id = None):
        """function for fetching messages"""
        res = {}
        if follower_search_id :
            domain = expression.AND([domain, expression.OR([
                [("author_id.id", "=", follower_search_id)],
            ])])

        if search_date:
            from_date_min = datetime.strptime(search_date, "%Y-%m-%d")
            from_date_max = from_date_min + timedelta(days=1)
            domain = expression.AND([domain, expression.AND([
                [("date", ">=", from_date_min)],
                [('date', "<", from_date_max)]
            ])])
        if search_term:
            if not follower_search_id and not search_date:
                search_term = search_term.replace(" ", "%")
                domain = expression.AND([domain, expression.OR([
                    # sudo: access to attachment is allowed if you have access to the parent model
                    [("attachment_ids", "in",
                      self.env["ir.attachment"].sudo()._search(
                          [("name", "ilike", search_term)]))],
                    [("body", "ilike", search_term)],
                    [("subject", "ilike", search_term)],
                    [("subtype_id.description", "ilike", search_term)],
                ])])
            domain = expression.AND([domain, [("message_type", "not in",
                                               ["user_notification",
                                                "notification"])]])

            res["count"] = self.search_count(domain)
        if around:
            messages_before = self.search(
                domain=[*domain, ('id', '<=', around)], limit=limit // 2,
                order="id DESC")
            messages_after = self.search(domain=[*domain, ('id', '>', around)],
                                         limit=limit // 2, order='id ASC')
            return {**res,
                    "messages": (messages_after + messages_before).
                    sorted('id', reverse=True)}
        if before:
            domain = expression.AND([domain, [('id', '<', before)]])
        if after:
            domain = expression.AND([domain, [('id', '>', after)]])

        res["messages"] = self.search(domain, limit=limit,
                                      order='id ASC' if after else 'id DESC')
        if after:
            res["messages"] = res["messages"].sorted('id', reverse=True)
        return res
