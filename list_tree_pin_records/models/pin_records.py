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


class PinRecord(models.Model):
    """Class is used to store pinned records in the database."""
    _name = 'pin.records'
    _description = 'Pin Records'

    record_id = fields.Integer(string="Record ID", help='Record ID.')
    res_model = fields.Char(string="Model", help='Corresponding model.')
    color = fields.Char(string="Color", help='Color code.')
    user_id = fields.Many2one('res.users', string='User',
                              help="Set current user.")

    @api.model
    def save_pin_record(self, pin_model):
        """Function to toggle pin status for a record."""
        if (
            not pin_model
            or not isinstance(pin_model, (list, tuple))
            or len(pin_model) < 2
        ):
            return self.browse()
        record_id = pin_model[0]
        res_model = pin_model[1]
        color = pin_model[2] if len(pin_model) > 2 else ''
        record = self.search([
            ('record_id', '=', record_id),
            ('res_model', '=', res_model),
            ('user_id', '=', self.env.uid),
        ])
        if record:
            record.unlink()
        else:
            self.create({
                'record_id': record_id,
                'res_model': res_model,
                'color': color,
                'user_id': self.env.uid,
            })
        return self.search([
            ('res_model', '=', res_model),
            ('user_id', '=', self.env.uid),
        ])

    @api.model
    def pin_record(self, pin_model):
        """Function to fetch id and color of the specified model."""
        pinned_records = []
        records = self.search([
            ('res_model', '=', pin_model),
            ('user_id', '=', self.env.uid),
        ])
        for record in records:
            pinned_records.append({
                'id': record.record_id,
                'color': record.color,
                'model': record.res_model,
            })
        return pinned_records
