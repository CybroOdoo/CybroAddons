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


class HospitalLaboratory(models.Model):
    """Class holding laboratory details"""
    _name = 'hospital.laboratory'
    _description = 'Hospital Laboratory'

    notes = fields.Text(help='Notes regarding the laboratory')
    image_130 = fields.Image(max_width=128, max_height=128, string='Image',
                             help='Image of the laboratory')
    phone = fields.Char(help='Phone number of laboratory')
    mobile = fields.Char(help='Mobile number of'
                               ' laboratory')
    email = fields.Char(help='Email of the laboratory')
    street = fields.Char(help='Street name of lab')
    street2 = fields.Char(help='Street2 name of lab')
    zip = fields.Char(help='Zip code of lab')
    city = fields.Char(help="City of lab")
    state_id = fields.Many2one("res.country.state",
                               help='State of lab')
    country_id = fields.Many2one('res.country',
                                 related='state_id.country_id',
                                 help='Country name of lab')
    note = fields.Text(help='Notes regarding lab')
    name = fields.Char(string='Lab Sequence', help='Sequence number for lab',
                       copy=False,
                       readonly=True, index=1, default=lambda self: 'New')
    technician_id = fields.Many2one('hr.employee',
                                    string="Lab in charge",
                                    domain=[
                                        ('job_title', '=', 'Lab Technician')],
                                    help='Name of the lab technician who has '
                                         'the in charge')

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('laboratory.sequence') or 'New'
        return super().create(vals_list)
