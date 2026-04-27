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
from odoo import api, fields, models


class FoBelongings(models.Model):
    """The details of property entered to the office"""
    _name = 'fo.belongings'
    _description = 'Fo Belongings'

    property_name = fields.Char(string="Property",
                                help='The name of the Property')
    property_count = fields.Char(string="Count", help='Count of property')
    number = fields.Integer(compute='_compute_number', store=True, string="Sl",
                            help='Serial number')
    visit_id = fields.Many2one('fo.visit', string="Belongings",
                               help='The Visitors to the Office')
    property_counter_id = fields.Many2one('fo.property.counter',
                                          string="Belongings")
    permission = fields.Selection([('0', 'Allowed'),
                                   ('1', 'Not Allowed'),
                                   ('2', 'Allowed With Permission'),
                                   ], string='Permission', required=True,
                                  index=True, default='0', tracking=True,
                                  help='The permissions for the belongings')

    @api.depends('visit_id', 'property_counter_id')
    def _compute_number(self):
        """Creates serial number when adding the property"""
        for rec in self:
            for visit in rec.mapped('visit_id'):
                number = 1
                for line in visit.belonging_ids:
                    line.number = number
                    number += 1
            for visit in rec.mapped('property_counter_id'):
                number = 1
                for line in visit.belonging_ids:
                    line.number = number
                    number += 1
