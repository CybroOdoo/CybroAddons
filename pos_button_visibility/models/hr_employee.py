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
from odoo import api, fields, models


class HrEmployee(models.Model):
    """Add POS configurations and buttons in the employee form view for pos_hr support."""
    _inherit = 'hr.employee'

    pos_config_ids = fields.Many2many(
        'pos.config',
        string="Point of Sale",
        help="POS configurations where button restrictions apply. If empty, restrictions apply to all."
    )
    pos_button_ids = fields.Many2many(
        'pos.button',
        string="POS Buttons",
        help="POS buttons that should be restricted for this employee."
    )

    @api.model
    def _load_pos_data_fields(self, config):
        result = super()._load_pos_data_fields(config)
        result += ['pos_button_ids', 'pos_config_ids']
        return result

    @api.model
    def _load_pos_data_read(self, records, config):
        read_records = super()._load_pos_data_read(records, config)
        for record, employee in zip(read_records, records.sudo()):
            if not record.get('pos_button_ids') and employee.user_id.pos_button_ids:
                record['pos_button_ids'] = employee.user_id.pos_button_ids.ids
            if not record.get('pos_config_ids') and employee.user_id.pos_config_ids:
                record['pos_config_ids'] = employee.user_id.pos_config_ids.ids
        return read_records
