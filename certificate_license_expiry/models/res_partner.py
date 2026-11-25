# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    certificate_count = fields.Integer(compute='_compute_total_certificates_count',
                                       groups="certificate_license_expiry.certificates_license_expiry_group_customer",
                                       help="Count of certificates")
    license_count = fields.Integer(compute='_compute_total_license_count',
                                   groups="certificate_license_expiry.certificates_license_expiry_group_customer",
                                   help="Count of license")

    def _compute_total_certificates_count(self):
        """We can get the count of certificates"""
        if not self.env.user.has_group(
            'certificate_license_expiry.certificates_license_expiry_group_customer'
        ):
            return
        for partner in self:
            partner.certificate_count = self.env[
                'certificate.certificate'].sudo().search_count([('customer_id', '=', partner.id)])

    _compute_certificate_count = _compute_total_certificates_count

    def _compute_total_license_count(self):
        """We can get the count of license"""
        if not self.env.user.has_group(
            'certificate_license_expiry.certificates_license_expiry_group_customer'
        ):
            return
        for partner in self:
            partner.license_count = self.env[
                'certificate.license'].sudo().search_count([('customer_id', '=', partner.id)])

    _compute_license_count = _compute_total_license_count

    def action_show_certificates(self):
        """We can see the certificate in tree and form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Certificates',
            'view_mode': 'list,form',
            'res_model': 'certificate.certificate',
            'domain': [('customer_id', '=', self.id)],
            'context': "{'create': False}",
        }

    def show_certificates(self):
        """Compatibility helper for action_show_certificates"""
        return self.action_show_certificates()

    def action_show_license(self):
        """We can see the certificate in tree and form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'License',
            'view_mode': 'list,form',
            'res_model': 'certificate.license',
            'domain': [('customer_id', '=', self.id)],
            'context': "{'create': False}",
        }

    def show_license(self):
        """Compatibility helper for action_show_license"""
        return self.action_show_license()
