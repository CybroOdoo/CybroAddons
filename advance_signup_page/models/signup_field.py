# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amal Varghese, Jumana Jabin MP (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class SignupFields(models.Model):
    """ Model for Signup Fields.This class represents the Signup Fields model
    for the Odoo website. It is used to define and manage the fields that
    users can sign up with."""
    _name = 'signup.field'
    _description = 'Signup Fields for Website'

    field_id = fields.Many2one(comodel_name='ir.model.fields',
                               string='Signup Field',
                               domain=[('model_id.model', '=', 'res.users'),
                                       ('ttype', 'in', ['char', 'integer',
                                                        'float', 'text', 'date',
                                                        'datetime',
                                                        'binary', 'boolean'])],
                               help='The field associated with the '
                                    'signup field.')
    name = fields.Char(string='Field Label',
                       related='field_id.field_description',
                       help='The label of the signup field.')
    placeholder = fields.Char(string='Placeholder',
                              help='The placeholder text for the '
                                   'signup field.')
    help_description = fields.Text(string='Help',
                                   help='Additional help or description '
                                        'for the signup field.')
    field_type = fields.Char(string='Field Type',
                             readonly=True,
                             help='The type of the signup field.')
    number_of_cols = fields.Selection(selection=[('2', '2'), ('3', '3'),
                                                 ('4', '4'), ('6', '6'),
                                                 ('12', '12')],
                                      string='Number of Columns',
                                      help='The number of columns for the '
                                           'signup field layout.')
    is_required = fields.Boolean(string='Is Required',
                                 help='Specifies if the signup field is '
                                      'required.')
    configuration_id = fields.Many2one(comodel_name='signup.configuration',
                                       help='The signup configuration '
                                            'associated with the signup field')

    @api.model_create_multi
    def create(self, vals_list):
        """Create records for the SignupFields model."""
        field_ids = [vals['field_id'] for vals in vals_list if
                     'field_id' in vals]
        field_types = self.env['ir.model.fields'].browse(field_ids).mapped(
            'ttype')
        for vals in vals_list:
            if 'field_id' in vals:
                vals['field_type'] = field_types[
                    field_ids.index(vals['field_id'])]
        records = super(SignupFields, self).create(
            [vals for vals in vals_list if 'field_id' in vals])
        return records

    def write(self, vals):
        """Override the function to update the field type while saving the
         record"""
        if 'field_id' in vals:
            vals['field_type'] = self.env['ir.model.fields'].browse(
                vals['field_id']).ttype
        return super(SignupFields, self).write(vals)
