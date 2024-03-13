# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import fields, models


class FoVisitor(models.Model):
    """The Details of the Visitor"""
    _name = 'fo.visitor'
    _description = 'Fo Visitor'

    name = fields.Char(string="Visitor", required=True,
                       help='The name of the visitor')
    visitor_image = fields.Binary(string='Image', attachment=True,
                                  help='Picture of the visitor')
    street = fields.Char(string="Street", help='The street from where he come')
    street2 = fields.Char(string="Street2",
                          help='The second street from where he come')
    zip = fields.Char(change_default=True, help='Zip code where he belongs')
    city = fields.Char(string='City', help='The city of the visitor')
    state_id = fields.Many2one("res.country.state", string='State',
                               ondelete='restrict', help='State of visitor')
    country_id = fields.Many2one('res.country', string='Country',
                                 ondelete='restrict',
                                 help='Country of the visitor')
    phone = fields.Char(string="Phone", required=True,
                        help='Phone number of the visitor')
    email = fields.Char(string="Email", required=True,
                        help='Email of the visitor')
    proof_id = fields.Many2one('id.proof', string="ID Proof",
                               help='Id proof the visitor')
    id_proof_no = fields.Char(string="ID Number",
                              help='Id proof number of visitor')
    company_info_id = fields.Many2one('res.partner', string="Company",
                                      help='Visiting persons company details')
    visit_count = fields.Integer(compute='_compute_visit_count',
                                 string='# Visits',
                                 help='The number of times the person visited'
                                      'office')

    _sql_constraints = [
        ('field_uniq_email_and_id_proof', 'unique (email,proof_id)',
         "Please give the correct data!")]

    def _compute_visit_count(self):
        """Will compute the number of times a person visited the office"""
        data = self.env['fo.visit'].search(
            [('visitor_id', 'in', self.ids), ('state', '!=', 'cancel')]).ids
        self.visit_count = len(data)
