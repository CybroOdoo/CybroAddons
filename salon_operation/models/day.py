from openerp import models, fields,api,http,SUPERUSER_ID,_


class Days(models.Model):
    _name = 'salon.day'
    _rec_name = 'display_booked'

    name = fields.Integer('Day')
    day_type = fields.Selection([('on', 'On'), ('off', 'Off')], default='on', string='On/Off')
    off_reason = fields.Char()
    period_lines = fields.One2many('salon.period', 'day_id')
    month_id = fields.Many2one('salon.month')

    @api.one
    def _get_booked(self):
        count = 0
        total = 0
        for Each_Line in self.period_lines:
            if Each_Line.period_type == 'on':
                if Each_Line.booked:
                    count += 1
                    total += 1
                else:
                    total += 1

        if count < total:
            self.booked = False
        else:
            self.booked = True

    booked = fields.Boolean('Fully Booked', compute='_get_booked')


    @api.one
    def _get_display_booked(self):
        count = 0
        for Each_Line in self.period_lines:
            if Each_Line.booked:
                count += 1
        if count < len(self.period_lines):
            self.display_booked = str(self.name)
        else:
            self.display_booked = str(self.name) + '- Fully Booked'

    display_booked = fields.Char(compute='_get_display_booked')

    # @api.one
    # def _get_day_stat(self):
    #     self.day_stat = self.days.day_type
    # day_stat = fields.Char(compute='_get_day_stat', string='On/Off')



#
#     day_stat = fields.Selection([('on', 'On'), ('off', 'Off')], default='on')

#     period_lines = fields.One2many('salon.day.line', 'day_id')
#
#     _sql_constraints = [
#         ('name_unique', 'unique(name)', 'This day is already exist !')]
#
#     @api.one
#     def get_day(self):
#         if self.name >0 and self.name <= 31:
#             return True
#         else:
#             return False
#
#     def check_day_valid(self, cr, uid, ids, context=None):
#         return self.get_day(cr, uid, ids, context)[0]
#
#     _constraints = [
#         (check_day_valid, 'You created an invalid day', ['name']),
#     ]
#
#
# class DayLines(models.Model):
#     _name = 'salon.day.line'
#
#     period_id = fields.Many2one('salon.period', string='Time')
#     # @api.one
#     # def _get_period_stat(self):
#     #     self.period_stat = self.period_id.period_type
#
#     # period_stat = fields.Char(compute='_get_period_stat', string='On/Off')
#     day_id = fields.Many2one('salon.day')
#     period_stat = fields.Selection([('on', 'On'), ('off', 'Off')], default='on')
#
