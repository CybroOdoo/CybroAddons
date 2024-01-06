# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class WorkoutPlanOption(models.Model):
    """This model workout plan option is used adding the option for the workout
    """
    _name = "workout.plan.option"
    _description = "Workout Option"
    _order = 'id'

    order_id = fields.Many2one('workout.plan', string='Workout'
                                                      ' Plan Reference',
                               ondelete='cascade',
                               index=True, help="Workout plan")
    name = fields.Text(string='Description', required=True,
                       help="Name of the workout plan option")
    exercise_id = fields.Many2one('gym.exercise', string='Exercises',
                                  required=True, help="Exercise for the plan")
    equipment_id = fields.Many2one('product.product',
                                   string='Equipment', required=True,
                                   tracking=True, help="Equipment for the "
                                                       "workout",
                                   domain="[('is_gym_product', '!=',False)]", )
    sets = fields.Integer(string="Sets", help="Number of sets")
    repeat = fields.Integer(string="Repeat", help="Number of repeat for cycle")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company,
                                 help="The current company")
