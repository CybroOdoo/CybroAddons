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
from odoo import api, fields, models
from odoo.exceptions import AccessError
from odoo.http import request


class UserSelection(models.TransientModel):
    """
        Model used for selecting a user and switching the active session user.
        _compute_access_ids:
            function to compute corresponding user groups
        action_switch:
            function for switching the user
    """
    _name = 'user.selection'
    _description = 'User Selection'

    user_id = fields.Many2one('res.users', string="User",
                              required=True,
                              help="Select the user here",
                              domain=lambda self: [
                                  ('id', '!=', self.env.user.id)])
    access_ids = fields.Many2many('res.groups',
                                 string="Group",
                                 compute='_compute_access_ids',
                                 help="User groups for the selection",
                                 readonly=True)

    @api.depends('user_id')
    def _compute_access_ids(self):
        """Compute access groups for the selected user"""
        for record in self:
            record.access_ids = record.user_id.group_ids if record.user_id else self.env['res.groups']

    def action_switch(self):
        """
        Summary:
            function for switching the user
        Return:
            Main login page after logged in
        """
        self.ensure_one()
        if not self.env.user._is_admin():
            raise AccessError(self.env._(
                "Only administrators can log in as another user."))
        session = request.session
        session.update({
            'previous_user': self.env.user.id,
        })
        session.authenticate_without_password(self.env.cr.dbname,
                                              self.user_id.login, self.env)
        return {
            'type': 'ir.actions.act_url',
            'url': '/',
            'target': 'self'
        }
