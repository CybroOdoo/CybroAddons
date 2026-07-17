# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
    """
    Main master data for visitors.
    Stores professional and contact details of people visiting the office.
    """
    _name = 'fo.visitor'
    _description = 'Visitor'

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
                               help='ID proof of the visitor')
    id_proof_no = fields.Char(string="ID Number",
                              help='Id proof number of visitor')
    company_info_id = fields.Many2one('res.partner', domain="[('is_company', '=', True)]", string="Company",
                                      help='Visiting persons company details')
    visit_count = fields.Integer(compute='_compute_visit_count',
                                 string='# Visits',
                                 help='The number of times the person visited '
                                      'office')

    _field_uniq_email_and_id_proof = models.Constraint(
        'unique (email, proof_id)',
        "Please give the correct data!",
    )

    def _compute_visit_count(self):
        """
        Compute the number of successful visits for this visitor.
        """
        for record in self:
            record.visit_count = self.env['fo.visit'].search_count(
                [('visitor_id', '=', record.id), ('state', '!=', 'cancel')])
