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

from odoo import fields, models, _


class WorkoutPlan(models.Model):
    _name = "workout.plan"
    _inherit = ["mail.thread", "mail.activity.mixin", "image.mixin"]
    _description = "Workout Plan"
    _rec_name = "name"

    name = fields.Char(string="Name")
    workout_days_ids = fields.Many2many("workout.days", string="Workout Days")
    workout_plan_option_ids = fields.One2many(
        'workout.plan.option', 'order_id', 'Optional Products Lines')

    def action_workout_plan(self):
        """ wizard opened to create my workout plans """
        wizard_form = self.env.ref('gym_mgmt_system.view_workout_plan_wizard',
                                   False)
        print(wizard_form, "fffff")
        view_id = self.env['workout.plan.wizard']
        vals = {
            'workout_plan': self.id,
        }
        new = view_id.create(vals)
        return {
            'name': _('Assign Workout Plan'),
            'type': 'ir.actions.act_window',
            'res_model': 'workout.plan.wizard',
            'res_id': new.id,
            'view_id': wizard_form.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }


class WorkoutPlanOption(models.Model):
    _name = "workout.plan.option"
    _description = "Workout Option"
    _order = 'id'

    order_id = fields.Many2one('workout.plan', 'Workout Plan Reference',
                               ondelete='cascade', index=True)
    name = fields.Text('Description', required=True)
    exercise_id = fields.Many2one('gym.exercise', 'Exercises', required=True)
    equipment_ids = fields.Many2one('product.product', string='equipment',
                                    required=True, tracking=True,
                                    domain="[('gym_product', '!=',False)]")
    sets = fields.Integer(string="Sets")
    repeat = fields.Integer(string="Repeat")


class WorkoutDays(models.Model):
    _name = "workout.days"
    _description = "Workout Days"
    _rec_name = "name"

    name = fields.Char('Workout days')


class MyWorkoutPlan(models.Model):
    _name = "my.workout.plan"
    _inherit = ["mail.thread", "mail.activity.mixin", "image.mixin"]
    _description = "My Workout Plan"
    _rec_name = "payment_term_id"

    payment_term_id = fields.Many2one('workout.plan', string="Name")
    assign_to = fields.Many2one('res.partner', string='Assign To',
                                domain="[('gym_member', '!=',False)]")
    from_date = fields.Date(string='Date From')
    to_date = fields.Date(string='Date To')
