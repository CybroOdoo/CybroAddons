# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import email_normalize


class RegisterVendor(models.TransientModel):
    """For Registration of Vendors"""
    _name = 'register.vendor'
    _description = 'Register Vendors'

    def default_is_registered(self):
        """Default value for is registered"""
        if self.env.context.get('active_model') == 'res.partner':
            if self.env['res.users'].search([(
                    'partner_id', '=', self.env.context.get('active_id'))]):
                return True
        return False

    is_registered = fields.Boolean(string='Registered',
                                   default=default_is_registered, readonly=1,
                                   help='Checking whether the partner'
                                        'registered or not')

    def action_create_user_portal(self):
        """Creating the portal user"""
        if self.env.context.get('active_model') == 'res.partner':
            partner = self.env['res.partner'].browse(
                self.env.context.get('active_id'))
            if not partner.email:
                raise ValidationError(_("Provide Email For Vendor"))
            user = self.env['res.users'].with_context(
                no_reset_password=True).sudo()._create_user_from_template({
                'email': email_normalize(partner.email),
                'login': email_normalize(partner.email),
                'partner_id': partner.id,
                'company_id': self.env.company.id,
                'company_ids': [(6, 0, self.env.company.ids)],
                'active': True
            })
            self._send_email(user)
            partner.sudo().write({'is_registered': True})

    def _send_email(self, user):
        """Send notification email to a new portal user"""
        self.ensure_one()
        return {
            'name': _('Portal Access Management'),
            'type': 'ir.actions.act_window',
            'res_model': 'portal.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_send_password_reset_portal(self):
        """Send password reset email"""
        if self.env.context.get('active_model') == 'res.partner':
            partner = self.env['res.partner'].browse(
                self.env.context.get('active_id'))
            user = self.env['res.users'].search([
                ('partner_id', '=', partner.id)])
            user.action_reset_password()
