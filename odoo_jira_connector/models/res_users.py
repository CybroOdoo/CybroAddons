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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging

from odoo import api, fields, models

from .jira_client import JIRA_ERRORS, JiraClient
from .res_config_settings import EMAIL_REGEX

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    """Extend users with Jira account synchronization."""
    _inherit = 'res.users'

    jira_user_key = fields.Char(help='Account ID of the matching Jira user.')

    @api.model_create_multi
    def create(self, vals_list):
        """Create users and, in Automatic mode, invite the internal users
        with an email login to Jira."""
        users = super().create(vals_list)
        client = JiraClient.for_automatic_sync(self.env)
        if client:
            for user in users.filtered(lambda u: not u.jira_user_key and not u.share
                                       and EMAIL_REGEX.match(u.login or '')):
                try:
                    user.jira_user_key = client.create_user(user.login, user.name)
                except (*JIRA_ERRORS, KeyError) as error:
                    _logger.error("Failed to create a Jira user for %s: %s",
                                  user.login, error)
        return users
