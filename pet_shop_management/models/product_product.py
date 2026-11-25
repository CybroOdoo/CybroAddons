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
from datetime import timedelta, date
from odoo import api, Command, fields, models
from odoo.exceptions import UserError


class Product(models.Model):
    """ Inheriting pets as product """
    _inherit = 'product.product'

    is_pet = fields.Boolean(
        string='Is Pet', default=False, index=True,
        help='Check this box to treat this product as a registered pet.'
    )
    age = fields.Float(
        compute='_compute_age', string='Age', readonly=True,
        help='Calculated age of the pet in years based on Date of Birth.'
    )
    month = fields.Integer(
        compute='_compute_age', string='Month', readonly=True,
        help='Calculated age in months (especially for pets under 1 year).'
    )
    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Sex', help='Biological sex or gender of the pet.')
    dob = fields.Date(
        string='Date Of Birth',
        help='Date of birth of the pet, used to automatically calculate age.'
    )
    pet_type_id = fields.Many2one(
        'pet.type', string='Pet Type', ondelete='set null',
        help='Select species or breed category of pet (e.g. Dog, Cat).'
    )
    color = fields.Char(
        string='Color',
        help='Coat color, pattern, or distinctive visual markings of the pet.'
    )
    stay = fields.Char(
        string='Stay',
        help='Designated room, kennel, or accommodation instructions.'
    )
    pet_seq = fields.Char(
        string='Pet Sequence No.', required=True, copy=False, readonly=True,
        index=True, default=lambda self: 'New',
        help="Unique alphanumeric reference code generated for the pet."
    )
    photo_one = fields.Binary(
        string='Photo 1',
        help='Primary identification image displayed on portal and reports.'
    )
    photo_two = fields.Binary(
        string='Photo 2', help='Secondary photo of the pet for gallery view.'
    )
    photo_three = fields.Binary(
        string='Photo 3', help='Additional profile photo of the pet.'
    )
    notes = fields.Text(
        string='Note',
        help="Special care, behavioral observations, and dietary notes."
    )
    veterinarian_id = fields.Many2one(
        'hr.employee', domain="[('is_veterinarian', '=', True)]",
        ondelete='set null', string='Veterinarian',
        help='Licensed veterinarian employee assigned as primary doctor.'
    )
    is_contact = fields.Boolean(
        string='Contact Owner on Distress', default=False,
        help='Enable if the owner requests to be contacted immediately if '
             'the pet shows reluctance, hesitation, or distress.'
    )
    is_allergy = fields.Boolean(
        string='Allergic to Medicine', default=False,
        help='Indicates whether pet has recorded reactions to medicine.'
    )
    is_reaction = fields.Boolean(
        string='Reaction to Vaccine', default=False,
        help='Indicates whether pet has prior adverse reactions to vaccines.'
    )
    previous_reactions = fields.Text(
        string='Previous Medical or Surgical Problems',
        help='Detailed record of past illnesses, surgeries, or conditions.'
    )
    pet_place = fields.Char(
        string='Where Did Your Pet Come From?', default='Pet Store',
        help='Origin or source of pet (e.g. Breeder, Shelter, Pet Store).'
    )
    pet_food = fields.Char(
        string='What Do You Feed Your Pet?',
        help='Specific dietary requirements, food brands, and routines.'
    )
    is_pet_service = fields.Boolean(
        string='Is Pet Service', default=False, index=True,
        help="Check this box if this product represents a pet care service."
    )
    pet_vaccines_ids = fields.One2many(
        'pet.vaccines', 'pet_vaccine_id', string='Pet Vaccines',
        help='Complete history of vaccinations and booster records for pet.'
    )
    vaccine = fields.Binary(
        string='Vaccine Card',
        help='Uploaded copy or photo of the official vaccination card.'
    )
    customer_id = fields.Many2one(
        'res.partner', string='Customer', index=True, ondelete='set null',
        help='Registered pet owner or customer responsible for this pet.',
        domain="[('type', '!=', 'private')]"
    )
    responsible_id = fields.Many2one(
        'res.users', string='Scheduler User',
        default=lambda self: self.env.user,
        required=True, ondelete='restrict',
        help='Internal user responsible for scheduling care for this pet.'
    )
    partner_id = fields.Many2one(
        'res.partner', string='Partner', required=False, ondelete='set null',
        help="Associated secondary contact partner or guardian."
    )
    is_sale_order = fields.Boolean(
        string='Sale Order Created', default=False, copy=False,
        help='Indicates whether a sales quotation or order has been generated.'
    )

    @api.depends('dob')
    def _compute_age(self):
        """ Computes pets age according to their dob """
        for rec in self:
            if rec.dob:
                rec.age = (date.today() - rec.dob) // timedelta(days=365.2425)
                rec.month = (date.today() - rec.dob) // timedelta(days=30)
            else:
                rec.age = False
                rec.month = False

    def create_sale_order(self):
        """ Creating sale order if there exists """
        partner = self.partner_id or self.customer_id
        if not partner:
            partner = self.env.user.partner_id

        sale = None
        if self.is_pet:
            if self.qty_available > 0:
                sale = self.env['sale.order'].create({
                    'partner_id': partner.id,
                })
                vals = {
                    'order_id': sale.id,
                    'product_id': self.id,
                    'product_template_id': self.product_tmpl_id.id,
                    'name': self.display_name or self.name,
                    'product_uom_qty': 1.0,
                    'price_unit': self.list_price,
                }
                sale.order_line = [Command.create(vals)]
            else:
                raise UserError(
                    self.env._("Available quantity is Zero."))
        elif self.is_pet_service:
            sale = self.env['sale.order'].create({
                'partner_id': partner.id,
            })
            vals = {
                'order_id': sale.id,
                'product_id': self.id,
                'product_template_id': self.product_tmpl_id.id,
                'name': self.display_name or self.name,
                'product_uom_qty': 1.0,
                'price_unit': self.list_price,
            }
            sale.order_line = [Command.create(vals)]
        else:
            raise UserError(
                self.env._("This action is only valid for pets or services."))

        self.is_sale_order = True
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        """ Inherited to generate pet sequence """
        for vals in vals_list:
            if vals.get('pet_seq', 'New') == 'New' and vals.get('is_pet'):
                vals['pet_seq'] = self.env['ir.sequence'].next_by_code(
                    'pet.sequence') or 'New'
        return super().create(vals_list)

    def _get_report_base_filename(self):
        """ Return base report name for customer portal download """
        self.ensure_one()
        return f"Pet - {self.pet_seq or self.name}"
