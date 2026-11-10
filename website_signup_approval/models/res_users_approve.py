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
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsersApprove(models.Model):
    """Store Signup Information of Users from Website"""
    _name = 'res.users.approve'
    _description = "Approval Request Details"

    name = fields.Char(help="Name of the applicant", string='Name')
    email = fields.Char(help="Email address of the applicant", string="Email")
    for_approval_menu = fields.Boolean(
        string='For Approval Menu',
        default=False, readonly=True,
        help="Indicates whether the request has been approved")
    approved_date = fields.Datetime(
        string='Approved Date', copy=False,
        help="Date and time when the signup request was approved")
    attachment_ids = fields.One2many(
        'user.approval.window',
        'approval_id',
        string='Attachments',
        help="Uploaded applicant documents")
    password = fields.Char(
        string='Password', copy=False,
        groups="base.group_system",
        help="Applicant's temporary password until approval")
    hide_button = fields.Boolean(
        string='Hide Action Buttons',
        default=False,
        help="Technical flag to hide action buttons after processing")

    @api.constrains('email')
    def _check_unique_email(self):
        """Ensure no duplicate approval request for the same email"""
        for record in self:
            if record.email:
                duplicate = self.search([
                    ('email', '=ilike', record.email.strip()),
                    ('id', '!=', record.id),
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        "An approval request for '%(email)s' already exists.",
                        email=record.email,
                    ))

    def action_approve_login(self):
        """To approve the request from website (multi-record safe)"""
        res_user = self.env['res.users']
        template = self.env.ref(
            'auth_signup.mail_template_user_signup_account_created',
            raise_if_not_found=False)
        for record in self:
            record.for_approval_menu = True
            record.hide_button = True
            record.approved_date = fields.Datetime.now()
            user = res_user.sudo().search(
                [('login', '=', record.email)], limit=1)
            # Read password via sudo so non-system approvers are not blocked
            sudo_rec = record.sudo()
            if not user:
                user_values = {
                    'login': record.email,
                    'name': record.name,
                    'group_ids': [
                        (4, self.env.ref('base.group_portal').id)],
                }
                user = res_user.sudo().create(user_values)
                if sudo_rec.password:
                    ctx = res_user._crypt_context()
                    pw = sudo_rec.password
                    pw_hash = (
                        ctx.hash(pw)
                        if ctx.identify(pw) == 'plaintext'
                        else pw
                    )
                    res_user.sudo()._set_encrypted_password(user.id, pw_hash)
                if template:
                    template.sudo().send_mail(
                        user.id,
                        email_values={'email_to': user.login},
                        force_send=True)
            elif sudo_rec.password:
                ctx = res_user._crypt_context()
                pw = sudo_rec.password
                pw_hash = (
                    ctx.hash(pw)
                    if ctx.identify(pw) == 'plaintext'
                    else pw
                )
                res_user.sudo()._set_encrypted_password(user.id, pw_hash)
            if sudo_rec.password:
                sudo_rec.password = False

    def action_reject_login(self):
        """To reject the request from website (multi-record safe)"""
        for record in self:
            was_approved = record.for_approval_menu
            record.for_approval_menu = False
            record.hide_button = True
            record.approved_date = False
            sudo_rec = record.sudo()
            if sudo_rec.password:
                sudo_rec.password = False
            if was_approved:
                user = self.env['res.users'].sudo().search(
                    [('login', '=', record.email)], limit=1)
                if (user and user.has_group('base.group_portal')
                        and not user._is_internal()
                        and not user._is_admin()):
                    user.unlink()
