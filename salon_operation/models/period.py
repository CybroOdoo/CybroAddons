from openerp import models, fields,api,http,SUPERUSER_ID,_
from openerp.http import request


class Period(models.Model):
    _name = 'salon.period'
    _rec_name = 'display_booked'

    name = fields.Float('Time')

    # _sql_constraints = [
    #     ('name_unique', 'unique(name)', 'This time is already exist !')]

    chair_lines = fields.One2many('salon.period.line', 'period_id')
    period_type = fields.Selection([('on', 'On'), ('off', 'Off')], default='on', string='On/Off')
    off_reason = fields.Char()
    day_id = fields.Many2one('salon.day')

    @api.one
    def _get_booked(self):
        count = 0
        for Each_Chair in self.chair_lines:
            if Each_Chair.partner_id.id:
                count += 1
        if count < len(self.chair_lines):
            self.booked = False
        else:
            self.booked = True
    booked = fields.Boolean('Fully Booked', compute='_get_booked')

    @api.one
    def _get_display_booked(self):
        count = 0
        for Each_Chair in self.chair_lines:
            if Each_Chair.partner_id.id:
                count += 1
        if count < len(self.chair_lines):
             self.display_booked = str(self.name)
        else:
            self.display_booked = str(self.name) + '  -Fully Booked'



    display_booked = fields.Char(compute='_get_display_booked')
    # @api.onchange('chair_lines')
    # def unique_chair(self):
    #     # GET VALUE TO CHILD CHAIR
    #     selected_chair = str(request.session.get('onchange_chair_selected'))
    #     request.session['onchange_chair_selected'] = None
    #     already_exist = 0
    #     for Each_Chair in self.chair_lines:
    #         if Each_Chair.chair_id.name == selected_chair:
    #             already_exist += 1
    #     if already_exist >= 2:
    #         return {'warning': {
    #             'title': _('Constraint Error'),
    #             'message': 'This chair is already selected for this period',
    #             }}


class PeriodLine(models.Model):
    _name = 'salon.period.line'

    chair_id = fields.Many2one('salon.chair', string='Chair')
    period_id = fields.Many2one('salon.period')
    partner_id = fields.Many2one('res.partner', string='Customer')

    @api.one
    def _get_related_emp(self):
        self.related_employee = self.chair_id.related_employee
    related_employee = fields.Many2one('hr.employee', compute='_get_related_emp', string='Dressing Person')

    @api.one
    def _get_booked(self):
        if self.partner_id:
            self.booked = True
        else:
            self.booked = False
    booked = fields.Boolean('Booked', compute='_get_booked')
    book_no = fields.Char('Booking No', default=' ')



