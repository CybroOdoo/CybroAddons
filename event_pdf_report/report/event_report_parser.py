# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2016-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.report import report_sxw
from openerp.osv import osv


class EventParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(EventParser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'event_attendee_details': self.event_attendee_details,
        })
        self.context = context

    def event_attendee_details(self, d):
        event = []

        obj_attendee = self.pool.get('event.registration').search(self.cr, self.uid, [('event_id', '=', d)])
        if obj_attendee:
            for obj in obj_attendee:
                obj_event = self.pool.get('event.registration').browse(self.cr, self.uid, obj, context=None)
                vals = {
                    'partner_id': obj_event.partner_id.name,
                    'date_open': obj_event.date_open,
                    'date_closed': obj_event.date_closed,
                    'state': obj_event.state,

                }
                event.append(vals)

            return event


class PrintReport(osv.AbstractModel):
    _name = 'report.event_pdf_report.report_event'
    _inherit = 'report.abstract_report'
    _template = 'event_pdf_report.report_event'
    _wrapped_report_class = EventParser
