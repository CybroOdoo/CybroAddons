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


class FreightTracking(models.TransientModel):
    _name = 'freight.order.track'
    _description = 'Freight Order Track'

    date = fields.Date(default=fields.Date.context_today)
    freight_id = fields.Many2one('freight.order', required=True)
    source_loc_id = fields.Many2one('freight.port', 'Source Location')
    destination_loc_id = fields.Many2one(
        'freight.port', 'Destination Location', required=True)
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], "Transport")
    type = fields.Selection([('received', 'Received'),
                             ('delivered', 'Delivered')], 'Received/Delivered',
                            required=True)
    company_id = fields.Many2one('res.company', copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda self: self.env.company)

    def action_order_submit(self):
        """Create tracking details of order and notify the partners"""
        self.ensure_one()
        self.env['freight.track'].create({
            'freight_id': self.freight_id.id,
            'source_loc_id': self.source_loc_id.id,
            'destination_loc_id': self.destination_loc_id.id,
            'transport_type': self.transport_type,
            'date': self.date,
            'type': self.type,
        })
        rec = self.freight_id
        status = dict(self._fields['type']._description_selection(self.env))[
            self.type]
        message = self.env._(
            "The Freight Order %(order)s is %(status)s at %(location)s",
            order=rec.name, status=status,
            location=self.destination_loc_id.name)
        partners = rec._get_notify_partners()
        # The body is plain text, so it is escaped by the mail thread. The
        # notification is queued, it is not sent synchronously.
        rec.with_context(mail_notify_force_send=False).message_post(
            subject=message, body=message, partner_ids=partners.ids,
            message_type='comment', subtype_xmlid='mail.mt_comment')
        return {'type': 'ir.actions.act_window_close'}
