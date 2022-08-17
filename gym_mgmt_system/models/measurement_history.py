# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shahul Faiz (<https://www.cybrosys.com>)
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

from odoo import api, fields, models


class MeasurementHistory(models.Model):
    _name = "measurement.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Measurement History"

    _rec_name = "member"

    def _get_default_weight_uom(self):
        """ to get default weight uom """
        return self.env[
            'product.template']._get_weight_uom_name_from_ir_config_parameter()

    member = fields.Many2one('res.partner', string='Member', tracking=True,
                             required=True,
                             domain="[('gym_member', '!=',False)]")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string="Gender", required=True)
    age = fields.Integer(string='Age', tracking=True, required=True)
    weight = fields.Float(
        'Weight', digits='Stock Weight', store=True)
    weight_uom_name = fields.Char(string='Weight unit of measure label',
                                  default=_get_default_weight_uom)
    height = fields.Float(
        'Height', digits='Stock Height', store=True)
    height_uom_name = fields.Char(string='Weight unit of measure label',
                                  default='cm')
    bmi = fields.Float('BMI', store=True, compute='compute_display_name')
    bmr = fields.Float('BMR', store=True, compute='compute_display_name')
    neck = fields.Float('neck', store=True)
    biceps = fields.Float('Biceps', store=True)
    calf = fields.Float('Calf', store=True)
    hips = fields.Float('Hips', store=True)
    chest = fields.Float('Chest', store=True)
    waist = fields.Float('Waist', store=True)
    thighs = fields.Float('Thighs', store=True)
    date = fields.Date(string='Date',
                       help='Date from which measurement active.')

    @api.depends('weight', 'height')
    def compute_display_name(self):
        """ based on weight and height ,calculate the bmi and bmr"""
        if self.weight and self.height:
            self.bmi = (self.weight / self.height / self.height) * 10000

            if self.gender == "male":
                self.bmr = 66.47 + (13.75 * self.weight) + \
                           (5.003 * self.height) - (6.755 * self.age)

            if self.gender == "female":
                self.bmr = 655.1 + (9.563 * self.weight) + \
                           (1.85 * self.height) - (6.755 * self.age)
