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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class WmPortalRequestRejectWizard(models.TransientModel):
    """Collects the reason for rejecting a customer service request."""
    _name = 'wm.portal.request.reject.wizard'
    _description = 'Reject Service Request Wizard'

    request_id = fields.Many2one('wm.portal.service.request', string='Service Request', required=True)
    reason = fields.Text(string='Reason', required=True)

    def action_reject(self):
        """Reject the request with the entered reason."""
        self.ensure_one()
        self.request_id.action_reject(reason=self.reason)
        return {'type': 'ir.actions.act_window_close'}
