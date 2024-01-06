# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Raneesha M K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ApplicationReject(models.TransientModel):
    """This model for providing a rejection explanation while
        rejecting an application."""
    _name = 'application.reject'
    _description = 'Choose Reject Reason'

    reject_reason_id = fields.Many2one('reject.reason',
                                       string="Rejecting reason",
                                       help="Select Reason for "
                                            "rejecting the Applications")

    def action_reject_reason_submit(self):
        """This method writes the reject reason selected by the user to the
            application record.It then calls the `action_reject` method to
            reject the application.

            :returns class: university.application, The rejected application.
        """
        for rec in self:
            application = self.env['university.application'].browse(
                self.env.context.get('active_ids'))
            application.write({'reject_reason': rec.reject_reason_id.id})
            return application.action_reject()
