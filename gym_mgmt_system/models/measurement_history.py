# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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


class MeasurementHistory(models.Model):
    """This model used for measurement history."""
    _name = "measurement.history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Measurement History"
    _rec_name = "member_id"

    def _get_default_weight_uom(self):
        """ to get default weight uom """
        return self.env[
            'product.template']._get_weight_uom_name_from_ir_config_parameter()

    member_id = fields.Many2one('res.partner', string='Member',
                                tracking=True, required=True,
                                domain="[('is_gym_member', '!=',False)]",
                                help='Name of the member')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string="Gender", required=True, help='Select the gender')
    age = fields.Integer(string='Age', tracking=True, required=True,
                         help='Age of the member')
    weight = fields.Float(
        'Weight', digits='Stock Weight',
        help='Define the your weight')
    weight_uom_name = fields.Char(string='Weight unit of measure label',
                                  default=_get_default_weight_uom,
                                  help='Weight of uom')
    height = fields.Float(
        'Height', digits='Stock Height', help='Define your '
                                              'height')
    height_uom_name = fields.Char(string='Height unit of measure label',
                                  default='cm', help='Uom for height')
    bmi = fields.Float(string='BMI', store=True,
                       compute='_compute_bmi_bmr', help='Calculate BMI')
    bmr = fields.Float(string='BMR', store=True,
                       compute='_compute_bmi_bmr',
                       help='Calculate BMR')
    neck = fields.Float(string='Neck', help='The length of neck')
    biceps = fields.Float(string='Biceps',
                          help='The length of biceps')
    calf = fields.Float(string='Calf', help='The length of calf')
    hips = fields.Float(string='Hips', help='The length of hips')
    chest = fields.Float(string='Chest',
                         help='The length of chest')
    waist = fields.Float(string='Waist',
                         help='The length of waist')
    thighs = fields.Float(string='Thighs',
                          help='The length of thighs')
    date = fields.Date(string='Date',
                       help='Date from which measurement active.')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help="This field hold the company id")

    @api.depends('weight', 'height', 'gender', 'age')
    def _compute_bmi_bmr(self):
        """Based on weight and height ,calculate the bmi and bmr"""
        for rec in self:
            rec.bmi = rec.bmr = 0
            if rec.weight and rec.height:
                rec.bmi = (rec.weight / rec.height / rec.height) * 10000
                if rec.gender == "male":
                    rec.bmr = 66.47 + (13.75 * rec.weight) + \
                               (5.003 * rec.height) - (6.755 * rec.age)
                if rec.gender == "female":
                    rec.bmr = 655.1 + (9.563 * rec.weight) + \
                               (1.85 * rec.height) - (6.755 * rec.age)
            else:
                rec.bmi = 1
                rec.bmr = 1
