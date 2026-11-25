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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class SittingSchedule(models.Model):
    """ Sitting Schedule for pets """
    _name = 'sitting.schedule'
    _description = 'Sitting Schedule'

    name = fields.Char(
        string='Name', required=True, default='Pet Sitting Schedule',
        help="Subject or title of this sitting appointment."
    )
    number_id = fields.Many2one(
        'sale.order', string='Sale Order', ondelete='set null',
        help='Originating sales quotation or order for this sitting schedule.'
    )
    date_start = fields.Datetime(
        string='Start Date', required=True, index=True,
        help='Scheduled start date and time for this sitting appointment.'
    )
    end_date = fields.Datetime(
        string='End Date', required=True, index=True,
        help='Scheduled end date and time when the sitting service concludes.'
    )
    attendees_ids = fields.Many2many(
        'hr.employee', domain="[('is_walker_sitters', '=', True)]",
        string='Attendees',
        help="Assigned employees attending to the pets during this schedule."
    )
    pet_info_ids = fields.One2many(
        'pet.info', 'info_pet_id', string='Pet Information',
        help='Detailed list of pets cared for during this sitting schedule.'
    )
    service_ids = fields.One2many(
        'pet.service', 'service_pet_id', string='Services',
        help='Specific pet care services provided during this visit.'
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
        ondelete='restrict',
        help='Operating company responsible for this sitting appointment.'
    )


class PetInfo(models.Model):
    """ Information of pets in sitting schedule """
    _name = 'pet.info'
    _description = 'Pet Information'

    info_pet_id = fields.Many2one(
        'sitting.schedule', string='Sitting Schedule', ondelete='cascade',
        help='Parent pet sitting appointment record this line belongs to.'
    )
    num = fields.Many2one(
        'product.product', domain="[('is_pet', '=', True)]",
        string='Pet', required=True, ondelete='cascade',
        help='Selected pet being cared for during this sitting session.'
    )
    pet_num = fields.Char(
        related='num.pet_seq', string='Reference', readonly=True,
        help='Auto-populated unique sequence reference code of the pet.'
    )
    name = fields.Char(
        related='num.name', string='Name', readonly=True,
        help='Name of the pet.'
    )
    age = fields.Float(
        related='num.age', string='Age', readonly=True,
        help='Current age of the pet in years.'
    )
    sex = fields.Selection(
        related='num.sex', string='Sex', readonly=True,
        help='Gender or sex of the pet.'
    )
    pet_type_id = fields.Many2one(
        'pet.type', related='num.pet_type_id', readonly=True,
        string='Pet Type', help='Species or breed classification of the pet.'
    )
    color = fields.Char(
        related='num.color', string='Color', readonly=True,
        help='Coat color, pattern, and distinctive markings of the pet.'
    )
    stay = fields.Char(
        related='num.stay', string='Stay', readonly=True,
        help='Designated kennel, room, or accommodation instructions.'
    )
    customer = fields.Many2one(
        'res.partner', string='Customer', ondelete='set null',
        help='Owner or primary customer responsible for this pet.'
    )


class PetService(models.Model):
    """ Pet Services in sitting schedule """
    _name = 'pet.service'
    _description = 'Pet Service'

    service_pet_id = fields.Many2one(
        'sitting.schedule', string='Service Pet', ondelete='cascade',
        help='Parent pet sitting appointment this service line belongs to.'
    )
    name = fields.Many2one(
        'product.product', domain="[('is_pet_service', '=', True)]",
        string='Service', required=True, ondelete='restrict',
        help='Select the pet care service product provided.'
    )
    cost = fields.Float(
        related='name.standard_price', string='Cost', readonly=True,
        help='Internal standard cost per unit for this service product.'
    )
    sale_price = fields.Float(
        related='name.list_price', string='Price', readonly=True,
        help='Customer sales price charged for this service.'
    )
