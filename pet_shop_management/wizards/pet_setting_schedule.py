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


class PetSittingSchedule(models.TransientModel):
    """Scheduling pet sittings"""
    _name = 'pet.sitting.schedule'
    _description = 'sitting_schedule'

    walker_sitting_id = fields.Many2one('hr.employee',
                                        domain="[('is_walker_sitters', '=', True)]",
                                        required=True, string="Walker",
                                        help='Walker/sitter of pets')
    schedule_description = fields.Char(string='Schedule Description',
                                       help='Description for schedule')
    attendees_ids = fields.One2many('attendees.pet',
                                    'attendee_id', string='Attendees',
                                    help='Attendees for the pet sitting schedules')
    date_start = fields.Datetime(string='Start Date', required=True,
                                 help='Starting date of scheduling')
    end_date = fields.Datetime(string='End Date', required=True,
                               help='Ending date of scheduling')
    reference_id = fields.Many2one('sale.order', string='Reference',
                                   help='Reference of the pet')
    pet_info_ids = fields.One2many('pet.info', 'info_id',
                                   string='Pet Information',
                                   help='Information of the pet')
    service_ids = fields.One2many('pet.service', 'pet_service_id',
                                  string='Service', help='Service pet')

    def assign_sittings(self):
        """Assigning pet sittings through wizards"""
        self.env['sitting.schedule'].create({
            'name': 'Meeting',
            'number_id': self.reference_id.id,
            'date_start': self.date_start,
            'end_date': self.end_date,
            'attendees_ids': [(4, self.walker_sitting_id.id)],
        })


class AttendeesPet(models.TransientModel):
    """Attendees of pet sittings"""
    _name = 'attendees.pet'

    attendee_id = fields.Many2one('pet.sitting.schedule',
                                  string='Related field',
                                  help='Related field of class PetSittingSchedule')
    attendees_id = fields.Many2one('res.partner', required=True,
                                   string='Attendees', help='Attendees')
    phone = fields.Char(related='attendees_id.phone', string='Phone',
                        help='Phone number of attendees')
    email = fields.Char(related='attendees_id.email', string='Email',
                        help='Email of attendees')


class PetInfo(models.TransientModel):
    """Information of pets"""
    _name = 'pet.info'

    info_pet_id = fields.Many2one('sitting.schedule', string='Sitting Schedule',
                                  help='Sitting schedule')
    num = fields.Many2one('product.product', domain="[('is_pet', '=', True)]",
                          string='Pet', help='Pet name')
    pet_num = fields.Char(related='num.pet_seq', string='Reference',
                          help='Pet reference')
    name = fields.Char(related='num.name', string='Name', help='Pet Name')
    info_id = fields.Many2one('pet.sitting.schedule', string='Pet Sitting',
                              help='Scheduled pet sittings')
    age = fields.Float(related='num.age', String='Age', help='Pet age')
    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Sex', help='Sex of the pet', related='num.sex')
    pet_type_id = fields.Many2one('pet.type', related='num.pet_type_id',
                                  string='Pet Type', help='Type of the pet')
    color = fields.Char(related='num.color', string='color', help='Pets color')
    stay = fields.Char(related='num.stay', string='Stay', help='Pet stay')
    customer = fields.Many2one('res.partner', string='Customer',
                               help='Customer of pets')


class PetService(models.TransientModel):
    """Pets as services"""
    _name = 'pet.service'
    _description = "Pet service"

    pet_service_id = fields.Many2one('pet.sitting.schedule',
                                     string='Pet Schedule', help='Pet schedule')
    service_pet_id = fields.Many2one('sitting.schedule', string='Service pet',
                                     help='Pet as service')
    name = fields.Many2one('product.product',
                           domain="[('is_pet_service', '=', True)]",
                           string='Name', help='Pet name')
    cost = fields.Float(related='name.list_price', string='cost',
                        help='Cost of the service')
    sale_price = fields.Float(related='name.standard_price', string='Price',
                              help='Price of service')
