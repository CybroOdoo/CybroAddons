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
from odoo import fields, models


class TokenInterface(models.Model):
    """Model to represent Token Interface"""
    _name = 'token.interface'
    _description = 'Token Interface'

    name = fields.Char()
    is_start_session = fields.Boolean(
        string="Session Started",
        help="Indicates whether an active session is currently running for this interface"
    )

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
