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
from odoo import  api, fields, models


class PatientRoom(models.Model):
    """Class holding Patient room details"""
    _name = 'patient.room'
    _description = 'Patient Room'

    name = fields.Char(help='The name of room', required=True)
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.company
                                  .currency_id.id,
                                  required=True, help='Currency in which '
                                                      'payments will be done')
    building_id = fields.Many2one('hospital.building',
                                  string="Block Name",
                                  required=True, help='Building to which '
                                                        'the room corresponds '
                                                        'to')
    nurse_ids = fields.Many2many('hr.employee',
                                 domain="[('job_id.name','=','Nurse')]",
                                 help='Nurses of the room')
    bed_type = fields.Selection([('gatch', 'Gatch Bed'),
                                 ('electric', 'Electric'),
                                 ('stretcher', 'Stretcher'),
                                 ('low', 'Low Bed'),
                                 ('air', 'Low Air Loss'),
                                 ('circo', 'Circo Electric'),
                                 ('clinitron', 'Clinitron'),
                                 ], help='Select the type '
                                                            'of bed')
    rent = fields.Monetary(help='Rent for the room')
    state = fields.Selection([('avail', 'Available'),
                              ('reserve', 'Reserve'),
                              ('not', 'Unavailable'), ],
                             readonly=True,
                             default="avail", help='State of room')
    room_facilities_ids = fields.Many2many('room.facility',
                                           string='Facilities',
                                           help='Facilities of room')
    floor_no = fields.Integer(string="Floor No.", help='The floor to '
                                                       'which the room '
                                                       'corresponds to')

    _name_uniq = models.Constraint(
        'unique (name)',
        "Room number should be unique!",
    )

    @api.model
    def fetch_rooms_details(self):
        """Function for fetch room details"""
        return self.sudo().search_read()
