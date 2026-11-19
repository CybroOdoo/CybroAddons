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


class AccountPaymentRegister(models.TransientModel):
    """
    Adding inpatient field to invoicing model.
    """
    _inherit = "account.payment.register"

    @api.model_create_multi
    def create(self, vals_list):
        """Create records to inpatient payment"""
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            partner_id = (vals.get('partner_id')
                          or (record.partner_id.id if record.partner_id else False))
            communication = (vals.get('communication')
                             or record.communication or 'Payment')
            amount = vals.get('amount') if 'amount' in vals else record.amount
            payment_date = (vals.get('payment_date')
                            or record.payment_date or fields.Date.today())
            if partner_id:
                inpatient = self.env['hospital.inpatient'].sudo().search([
                    ('patient_id', '=', partner_id)
                ], order='create_date desc', limit=1)
                if inpatient:
                    self.env['inpatient.payment'].sudo().create({
                        'name': communication,
                        'subtotal': amount,
                        'inpatient_id': inpatient.id,
                        'date': payment_date,
                    })
        return records
