"""Pet sitting schedule"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class SittingSchedule(models.Model):
    """Sitting Schedule wizards"""
    _name = 'sitting.schedule'
    _description = 'Sitting Schedule'

    name = fields.Char(string='Name', help="Name")
    number_id = fields.Many2one('sale.order', string='Number',
                                help='Sale order reference')
    date_start = fields.Date(string='Start Date',
                             help='Start date of sitting schedule')
    end_date = fields.Date(string='End Date',
                           help='End date of sitting schedule')
    attendees_ids = fields.Many2many('hr.employee',
                                     domain="[('is_walker_sitters', '=', True)]",
                                     string='Attendees',
                                     help="The attendees of the sitting "
                                          "schedule")
    duration = fields.Datetime(sting='Duration',
                               help='Duration of the schedule')
    pet_info_ids = fields.One2many('pet.info',
                                   'info_pet_id', string='Pet info',
                                   help='Information regarding the pets')
    service_ids = fields.One2many('pet.service',
                                  'service_pet_id',
                                  string='Service', help='Service information')
