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
from odoo import fields, models


class SelectDepartment(models.TransientModel):
    """ Transient model to select the department and counter"""
    _name = 'select.department'
    _description = 'Select Department'

    department_id = fields.Many2one('queue.department',
                                    help="Select the department")
    counter_id = fields.Many2one('queue.counter',
                                 help='Shows the corresponding counter')

    def action_submit(self):
        """Open the queue counter URL."""
        return {
            'type': 'ir.actions.act_url',
            'url': f'/queue/counter/{self.department_id.id}/{self.counter_id.id}',
            'target': 'new',

        }