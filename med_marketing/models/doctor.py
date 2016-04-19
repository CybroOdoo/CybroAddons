from openerp import models, fields, api
import datetime
from dateutil import parser


class Doctors(models.Model):
    _inherit = 'res.partner'

    doctor = fields.Boolean('Doctor')
    specialist_in = fields.Many2one('pha_marketing.departments', 'Specialist in')
    related_rep = fields.Many2one('hr.employee', string='Related Rep.', domain="[('rep','=',True)]")
    target = fields.Integer('Target')

    @api.one
    def _get_total_sale(self):
        total = 0.0
        created_domain = [('type', 'in', ['out_invoice', 'out_refund']), ('state', 'not in', ['draft', 'cancel']), ]
        for EACH_REPORT in self.env['account.invoice.report'].search(created_domain):
            if self.zip == EACH_REPORT.partner_id.zip:
                if self.specialist_in.id in EACH_REPORT.product_id.uses_in.ids:
                    if parser.parse(EACH_REPORT.date).month == datetime.date.today().month:
                        total_doctor = 0
                        for EACH_Doctor in self.search([('doctor', '=', True)]):
                            if EACH_Doctor.zip == self.zip and EACH_Doctor.specialist_in.id in EACH_REPORT.product_id.uses_in.ids:

                                total_doctor += 1
                        if total_doctor != 0:
                            total += (EACH_REPORT.price_total/total_doctor)


        self.total_sale = total
    total_sale = fields.Integer('Total sale', compute='_get_total_sale', help='Will calculate the doctors by considering zip code of both Doctors and Retailers and compare the department of doctor with use of sold medicines.')

