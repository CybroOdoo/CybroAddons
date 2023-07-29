# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: LAJINA.K.V (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LegalEvidence(models.Model):
    """Creation of legal evidence"""
    _name = 'legal.evidence'
    _description = 'legal evidence'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Reference', copy=False, readonly=True,
                       default=lambda x: _('New'))
    case_id = fields.Many2one("case.registration", "Case",
                              help='Name for cases',
                              required=True,
                              domain="[('state', 'not in',"
                                     "['won', 'lost','invoiced'])]")
    in_favor_id = fields.Many2one("res.partner", string="In Favor",
                                  help=' Name of in favor for the evidence',
                                  required=True)
    client_id = fields.Many2one(related="case_id.client_id", string="Client",
                                help='Clients for the evidence')
    description = fields.Text(help='Description of evidence')
    attachment_count = fields.Integer(compute='_compute_attachment_count',
                                      help="Count of attachments")

    @api.model
    def create(self, vals):
        """Generate Sequence For Evidence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'case_evidence') or 'New'
        return super(LegalEvidence, self).create(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancel(self):
        """ Records can't be deleted"""
        raise UserError(_("You can not delete a evidence"))

    def get_evidence_attachments(self):
        """Get the corresponding attachments of evidence"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachments',
            'view_mode': 'kanban,form',
            'res_model': 'ir.attachment',
            'domain': [('res_id', '=', self.id),
                       ('res_model', '=', self._name)],
            'context': "{'create': False}"
        }

    def _compute_attachment_count(self):
        """Compute the count of attachments"""
        for attachment in self:
            attachment.attachment_count = self.env['ir.attachment']. \
                sudo().search_count([('res_id', '=', self.id),
                                     ('res_model', '=', self._name)])
