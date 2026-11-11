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


class RenewWizard(models.TransientModel):
    _name = "agreement.renewal"
    _description = "Agreement Renewal Wizard"

    def _get_renewal_date(self):
        """Method for getting the renewal date"""
        agreements = self.env['purchase.recurring.agreement'].browse(
            self.env.context.get('active_ids', []))
        return agreements[:1].next_expiration_date

    date = fields.Date(
        string='Renewal Date', required=True,
        help="Effective date of the renewal. This date is the one taken into "
             "account in the next renewal",
        default=lambda self: self._get_renewal_date())
    comments = fields.Char(
        size=200, help='Renewal comments')

    def create_renewal(self):
        """Method for renewal of purchase recurring agreement"""
        self.ensure_one()
        agreement_ids = self.env.context.get('active_ids', [])
        for agreement_id in agreement_ids:
            self.env['purchase.agreement.renewal'].create(
                {'recurring_agreement_id': agreement_id,
                 'date': self.date,
                 'comments': self.comments})
        self.env['purchase.recurring.agreement'].browse(agreement_ids).write(
            {'last_renovation_date': self.date,
             'renewal_state': 'renewed'})
        return True
