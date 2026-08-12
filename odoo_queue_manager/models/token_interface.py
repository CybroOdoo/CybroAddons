# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models


class TokenInterface(models.Model):
    """Model to represent Token Interface"""
    _name = 'token.interface'

    name = fields.Char(string="Name")
    is_start_session = fields.Boolean(string='Is Start session',
                                      help="whether a new session is started "
                                           "or not")

    def action_start_new_session(self):
        """Function to start the new session"""
        self.env['token.session'].create({
            'name': self.name
        })
        self.is_start_session = True
        return {
            'type': 'ir.actions.act_url',
            'url': '/generate/token',
            'target': 'new',
        }

    def action_resume_session(self):
        """Function to resume session"""
        return {
            'type': 'ir.actions.act_url',
            'url': '/generate/token',
            'target': 'new',
        }

    def action_close_session(self):
        """Function to close session"""
        self.is_start_session = False
