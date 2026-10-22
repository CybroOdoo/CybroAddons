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
from odoo import models, fields


class QueueCounter(models.Model):
    """Model representing a queue counter"""
    _name = 'queue.counter'
    _description = 'Queue Counter'

    name = fields.Char(string="Counter Name", required=True, help="Name of the service counter")

    def action_start_process(self):
        """ Function to get the select department wizard"""
        return {
            'name': 'Start Processing',
            'type': 'ir.actions.act_window',
            'res_model': 'select.department',
            'view_mode': 'form',
            'context': {
                'default_counter_id': self.id},
            'target': 'new'
        }
