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

from odoo import fields, models


class WorkoutPlanWizard(models.TransientModel):
    _name = 'workout.plan.wizard'

    assign_to = fields.Many2one('res.partner', string='Assign To',
                                domain="[('gym_member', '!=',False)]")
    workout_plan = fields.Many2one('workout.plan', string='Workout Plan',
                                   required=True, readonly=True)
    from_date = fields.Date(string='Date From')
    to_date = fields.Date(string='Date To')

    def action_workout(self):
        """ create my workout plan of assign members only"""
        my_workout_plan = {
            'payment_term_id': self.workout_plan.id,
            'assign_to': self.assign_to.id,
            'from_date': self.from_date,
            'to_date': self.to_date,
        }
        record = self.env['my.workout.plan'].create(my_workout_plan)
        return record
