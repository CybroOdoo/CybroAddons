
from odoo import api, fields, models, _


class OngoingSession(models.TransientModel):
    _name = 'pos.sale.ongoing.wizard'
    _description = 'Point of Sale Ongoing Session Report'

    session_ids = fields.Many2many('pos.session', string='POS Sessions', domain=[('state', '=', 'opened')])

    def generate_report(self):
        data = {'session_ids': self.session_ids.ids}
        return self.env.ref('advanced_pos_reports.pos_ongoing_session_report').report_action([], data=data)

