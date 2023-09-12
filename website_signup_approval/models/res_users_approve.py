# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ResUsersApprove(models.Model):
    """Store Signup Information of Users from Website"""
    _name = 'res.users.approve'
    _description = "Approval Request Details"

    name = fields.Char(help="name of the user", string='Name')
    email = fields.Char(help="email of the user", string="Email")
    password = fields.Char(help="password of the user", string="Password")
    for_approval_menu = fields.Boolean(string='For Approval menu',
                                       default=False,
                                       help="Check the request is approved")
    approved_date = fields.Datetime(string='Approved Date', copy=False,
                                    help="Approval date of signup request")
    attachment_ids = fields.One2many('user.approval.window',
                                     'approval_id',
                                     string='Attachments',
                                     help="Store uploaded document")

    def action_approve_login(self):
        """To approve the request from website"""
        self.for_approval_menu = True
        user = self.env['res.users'].sudo().search([('login', '=', self.name)])
        if not user:
            user = self.env['res.users'].sudo().create({
                'login': self.name,
                'name': self.email,
                'password': self.password,
                'groups_id': [(4, self.env.ref('base.group_portal').id)]
            })
            template = self.env.ref(
                'auth_signup.mail_template_user_signup_account_created',
                raise_if_not_found=False)
            email_values = {
                'email_to': user.login,
            }
            template.send_mail(user.id, email_values=email_values,
                               force_send=True)

    def action_reject_login(self):
        """To reject the request from website"""
        self.for_approval_menu = False
        user = self.env['res.users'].sudo().search([('login', '=', self.name)])
        if user:
            user.unlink()
