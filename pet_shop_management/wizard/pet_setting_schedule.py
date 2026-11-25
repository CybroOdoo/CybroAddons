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
from odoo import Command, fields, models


class PetSittingSchedule(models.TransientModel):
    """ Scheduling pet sittings wizard """
    _name = 'pet.sitting.schedule'
    _description = 'Pet Sitting Schedule Wizard'

    walker_sitting_id = fields.Many2one(
        'hr.employee', domain="[('is_walker_sitters', '=', True)]",
        required=True, string="Walker", ondelete='cascade',
        help='Select employee walker or sitter for this appointment.'
    )
    schedule_description = fields.Char(
        string='Schedule Description',
        help='Custom title or description for sitting appointment.'
    )
    attendees_ids = fields.One2many(
        'attendees.pet', 'attendee_id', string='Attendees',
        help='Additional partner contacts attending the pet sitting session.'
    )
    date_start = fields.Datetime(
        string='Start Date', required=True,
        help='Beginning date and time when the pet sitting service commences.'
    )
    end_date = fields.Datetime(
        string='End Date', required=True,
        help='Concluding date and time when the pet sitting service concludes.'
    )
    reference_id = fields.Many2one(
        'sale.order', string='Reference', ondelete='cascade',
        help='Sales quotation or order linked to this scheduling wizard.'
    )
    pet_info_ids = fields.One2many(
        'pet.sitting.schedule.pet', 'wizard_id', string='Pet Information',
        help='Pets included in this sitting schedule.'
    )
    service_ids = fields.One2many(
        'pet.sitting.schedule.service', 'wizard_id', string='Service',
        help='Care services requested for this sitting session.'
    )

    def assign_sittings(self):
        """ Assigning pet sittings from sale order """
        sale_order = self.reference_id
        if sale_order:
            default_desc = self.env._('Pet Sitting - %s', sale_order.name)
        else:
            default_desc = self.env._('Pet Sitting')
        description = self.schedule_description or default_desc

        attendees = (
            [Command.link(self.walker_sitting_id.id)]
            if self.walker_sitting_id else []
        )

        pet_lines = [
            Command.create({
                'num': line.num.id,
                'customer': line.customer.id or (
                    sale_order.partner_id.id if sale_order else False
                ),
            }) for line in self.pet_info_ids
        ]

        service_lines = [
            Command.create({'name': line.name.id})
            for line in self.service_ids
        ]

        schedule_vals = {
            'name': description,
            'number_id': sale_order.id if sale_order else False,
            'date_start': self.date_start,
            'end_date': self.end_date,
            'attendees_ids': attendees,
            'pet_info_ids': pet_lines,
            'service_ids': service_lines,
        }
        schedule = self.env['sitting.schedule'].create(schedule_vals)
        return {
            'name': self.env._('Pet Sitting Schedule'),
            'type': 'ir.actions.act_window',
            'res_model': 'sitting.schedule',
            'res_id': schedule.id,
            'view_mode': 'form',
            'target': 'current',
        }


class PetSittingSchedulePet(models.TransientModel):
    """ Pet lines in the sitting wizard """
    _name = 'pet.sitting.schedule.pet'
    _description = 'Pet Sitting Schedule Wizard Pet Line'

    wizard_id = fields.Many2one(
        'pet.sitting.schedule', string='Wizard', ondelete='cascade',
        help='Parent sitting schedule wizard.'
    )
    num = fields.Many2one(
        'product.product', domain="[('is_pet', '=', True)]",
        string='Pet', required=True, ondelete='cascade',
        help='Pet product record associated with this line.'
    )
    pet_num = fields.Char(
        related='num.pet_seq', string='Reference', readonly=True,
        help='Unique sequence reference code of the pet.'
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
        string='Pet Type', help='Species or breed category of the pet.'
    )
    color = fields.Char(
        related='num.color', string='Color', readonly=True,
        help='Coat color and distinctive markings of the pet.'
    )
    stay = fields.Char(
        related='num.stay', string='Stay', readonly=True,
        help='Housing, kennel, or stay instructions for the pet.'
    )
    customer = fields.Many2one(
        'res.partner', string='Customer', ondelete='set null',
        help='Owner or primary customer of the pet.'
    )


class PetSittingScheduleService(models.TransientModel):
    """ Service lines in the sitting wizard """
    _name = 'pet.sitting.schedule.service'
    _description = 'Pet Sitting Schedule Wizard Service Line'

    wizard_id = fields.Many2one(
        'pet.sitting.schedule', string='Wizard', ondelete='cascade',
        help='Parent sitting schedule wizard.'
    )
    name = fields.Many2one(
        'product.product', domain="[('is_pet_service', '=', True)]",
        string='Service', required=True, ondelete='cascade',
        help='Pet care service product to be performed during sitting.'
    )
    cost = fields.Float(
        related='name.standard_price', string='Cost', readonly=True,
        help='Internal standard cost per unit for this service.'
    )
    sale_price = fields.Float(
        related='name.list_price', string='Price', readonly=True,
        help='Customer sales price charged for this service.'
    )


class AttendeesPet(models.TransientModel):
    """ Attendees of pet sittings """
    _name = 'attendees.pet'
    _description = 'Attendees Pet'

    attendee_id = fields.Many2one(
        'pet.sitting.schedule', string='Sitting Schedule', ondelete='cascade',
        help='Parent pet sitting schedule wizard reference.'
    )
    attendees_id = fields.Many2one(
        'res.partner', required=True, string='Attendees', ondelete='cascade',
        help='Partner contact or guardian attending the schedule.'
    )
    phone = fields.Char(
        related='attendees_id.phone', string='Phone', readonly=True,
        help='Contact phone number of the attendee.'
    )
    email = fields.Char(
        related='attendees_id.email', string='Email', readonly=True,
        help='Email address of the attendee.'
    )
