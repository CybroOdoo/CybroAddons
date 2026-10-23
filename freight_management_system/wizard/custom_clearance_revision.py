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


class CustomClearanceRevision(models.TransientModel):
    """Create Revision for the custom clearance"""
    _name = 'custom.clearance.revision'
    _description = 'Custom Clearance Revision Wizard'

    name = fields.Text(string='Reason', required=True,
                       help='Mention the reason for revision')
    custom_id = fields.Many2one('custom.clearance', string='Custom clearance',
                                required=True,
                                help='Select the custom clearance')
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda self: self.env.company)

    def action_create_revision(self):
        """Create revision against custom clearance and notify the agent"""
        self.ensure_one()
        clearance = self.custom_id
        self.env['clearance.revision'].create({
            'clearance_id': clearance.id,
            'reason': self.name,
            'name': self.env._("Revision for %s", clearance.name),
        })
        agent = clearance.agent_id
        if agent.email:
            message = self.env._(
                "Hi %(agent)s, the Custom Clearance %(clearance)s of the "
                "Freight Order %(order)s has a revision with the reason: "
                "%(reason)s",
                agent=agent.name, clearance=clearance.name,
                order=clearance.freight_id.name, reason=self.name)
            # The body is plain text, so it is escaped by the mail thread.
            # The notification is queued, it is not sent synchronously.
            clearance.with_context(mail_notify_force_send=False).message_post(
                subject=self.env._(
                    "Custom Clearance Revision For %s",
                    clearance.freight_id.name),
                body=message, partner_ids=agent.ids,
                message_type='comment', subtype_xmlid='mail.mt_comment')
        return {'type': 'ir.actions.act_window_close'}
