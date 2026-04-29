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
import logging
from odoo import models
from odoo.osv import expression
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class MailMessage(models.Model):
    """Inherited message model for super the _message_fetch """
    _inherit = 'mail.message'

    def _message_fetch(self, domain, search_term=None, before=None, after=None,
                       around=None, limit=30, search_date=None,
                       follower_search_id = None):
        """function for fetching messages"""
        _logger.info("ChatterFilter: _message_fetch called - term: %s, date: %s, follower: %s", 
                     search_term, search_date, follower_search_id)
        
        res = {}
        filter_domain = []
        if follower_search_id:
            filter_domain = expression.AND([filter_domain, [("author_id", "=", int(follower_search_id))]])

        if search_date:
            try:
                from_date_min = datetime.strptime(search_date, "%Y-%m-%d")
                from_date_max = from_date_min + timedelta(days=1)
                filter_domain = expression.AND([filter_domain, expression.AND([
                    [("date", ">=", from_date_min)],
                    [('date', "<", from_date_max)]
                ])])
            except Exception as e:
                _logger.error("ChatterFilter: Date parsing error: %s", e)
        
        if filter_domain:
            domain = expression.AND([domain, filter_domain])

        if search_term:
            search_query = expression.OR([
                    [("attachment_ids", "in",
                      self.env["ir.attachment"].sudo()._search(
                          [("name", "ilike", search_term.replace(" ", "%"))]))],
                    [("body", "ilike", search_term)],
                    [("subject", "ilike", search_term)],
                    [("subtype_id.description", "ilike", search_term)],
                ])
            domain = expression.AND([domain, search_query])
            
        _logger.info("ChatterFilter: Calculated Domain: %s", domain)

        if search_term or follower_search_id or search_date:
            res["count"] = self.search_count(domain)
            _logger.info("ChatterFilter: Count result: %s", res["count"])

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
        _logger.info("ChatterFilter: Found %s messages", len(res["messages"]))
        
        if after:
            res["messages"] = res["messages"].sorted('id', reverse=True)
        return res
