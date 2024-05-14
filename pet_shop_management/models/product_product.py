"""Pets"""
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
from datetime import timedelta, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Product(models.Model):
    """Inheriting pets as product"""
    _inherit = 'product.product'

    is_pet = fields.Boolean(string='Is Pet',
                            help='This is used to identify the pet')
    image_1920 = fields.Image(string="Image", help='This is the image of pet',
                              compute='_compute_image_1920',
                              inverse='_set_image_1920')
    age = fields.Float(compute='_compute_age', string='Age',
                       help='Age of the pet')
    sex = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], string='Sex', help='Sex of the pet')
    dob = fields.Date(string='Date Of Birth', help='Date of birth of pet')
    pet_type_id = fields.Many2one('pet.type', string='Pet Type',
                                  help='Type of the pet')
    color = fields.Char(string='Color', help='Color of the pet')
    stay = fields.Char(string='Stay', help='Stay of the pet')
    pet_seq = fields.Char(string='Pet No.', required=True,
                          copy=False,
                          readonly=True,
                          index=True,
                          default=lambda self: 'New')
    photo_one = fields.Binary(string='Image', help='Additional photo of pet')
    photo_two = fields.Binary(string='Image', help='Additional photo of pet')
    photo_three = fields.Binary(string='Image', help='Additional photo of pet')
    notes = fields.Text(string='Note', help="Additional notes")
    veterinarian_id = fields.Many2one('hr.employee',
                                      domain="[('is_veterinarian', '=', True)]",
                                      string='Veterinarian',
                                      help='Veterinarian of the pet')
    is_contact = fields.Boolean(string='Contact if your pet has any hesitation',
                                help='To know the pets hesitation')
    is_allergy = fields.Boolean(
        string='Has your pet ever had any allergic reaction to a medicine?',
        help='To know pets allergic reaction')
    is_reaction = fields.Boolean(
        string='Has your pet ever had a reaction to a vaccine?',
        help='To know the reaction to the vaccine.')
    previous_reactions = fields.Text(
        string='Has Your pet had any previous medical or surgical problems?',
        help='To know the pets surgical problems')
    pet_place = fields.Char(string='Where did your pet come from',
                            default='Pet Store',
                            help='Where did your pet come from')
    pet_food = fields.Char(string='what do you feed your pet',
                           help='What do you feed your pet')
    is_pet_service = fields.Boolean(string='Is pet Service',
                                    help="pet as service")
    pet_vaccines_ids = fields.One2many('pet.vaccines',
                                       'pet_vaccine_id',
                                       string='Pet Vaccines',
                                       help='Pet vaccines')
    vaccine = fields.Binary(string='Image', help='To upload the vaccine info')
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  help='Customer of thr pet',
                                  domain="[('type', '!=', 'private')]")
    responsible_id = fields.Many2one('res.users', string='Scheduler User',
                                     default=lambda self: self.env.user,
                                     required=True,
                                     help='Responsible for the pet')
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 required=True)
    is_sale_order = fields.Boolean(string='Sale Order', default=False)
    month = fields.Integer(string='Month', help='If the pet is below one year',
                           compute="_compute_age")

    @api.depends('dob')
    def _compute_age(self):
        """Computes pets age according to their dob"""
        for rec in self:
            if rec.dob:
                rec.age = (date.today() - rec.dob) // timedelta(days=365.2425)
                rec.month = (date.today() - rec.dob) // timedelta(days=30)
            else:
                rec.age = False
                rec.month = False

    def create_sale_order(self):
        """Creating sale order if there is exist"""
        onhand = self.env['stock.quant'].search([
            ('product_id', '=', self.id)])
        if len(onhand) != 0:
            sale = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
            })
            sale.order_line = [(5, 0, 0)]
            vals = {
                'order_id': sale.id,
                'product_id': self.id,
                'product_template_id': self.product_tmpl_id.id,
                'name': self.product_tmpl_id.name,
            }
            sale.order_line = [(0, 0, vals)]
        else:
            raise UserError(
                _("There is no pets to sell(Available quantity is Zero)"))
        return {
            'type': 'ir.actions.act_window',
            'target': 'current',
            'name': _('Create Sale'),
            'res_id': sale.id,
            'view_mode': 'form',
            'res_model': 'sale.order',
        }

    @api.model
    def create(self, vals):
        """To create the sequence"""
        if vals.get('pet_seq', 'New') == 'New':
            vals['pet_seq'] = self.env['ir.sequence'].next_by_code(
                'pet.sequence') or 'New'
        result = super().create(vals)
        return result
