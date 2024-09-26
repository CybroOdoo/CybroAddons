# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, api, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    certificate_count = fields.Integer(string="Certificate Count",
                                       compute='_compute_total_certificates'
                                               '_count',
                                       help="Count of certificates")
    license_count = fields.Integer(string="License Count",
                                   compute='_compute_total_license_count',
                                   help="Count of license")

    @api.depends('license_count')
    def _compute_total_certificates_count(self):
        """We can get the count of certificates"""
        self.certificate_count = self.env[
            'certificates'].search_count([('customer_id', '=', self.id)])

    @api.depends('certificate_count')
    def _compute_total_license_count(self):
        """We can get the count of license"""
        self.license_count = self.env[
            'license'].search_count([('customer_id', '=', self.id)])

    def show_certificates(self):
        """We can see the certificate in tree and form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Certificates',
            'view_mode': 'tree,form',
            'res_model': 'certificates',
            'domain': [('customer_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def show_license(self):
        """We can see the certificate in tree and form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'License',
            'view_mode': 'tree,form',
            'res_model': 'license',
            'domain': [('customer_id', '=', self.id)],
            'context': "{'create': False}"
        }
