from openerp import models, fields,api,http,SUPERUSER_ID


class Months(models.Model):
    _name = 'salon.month'
    _rec_name = 'display_booked'

    name = fields.Char('Name')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'This month is already exist !')]


    month = fields.Integer('Month')
    year = fields.Integer('Year')
    day_lines = fields.One2many('salon.day', 'month_id')

    @api.one
    def _get_booked(self):
        count = 0
        total = 0
        for Each_Day in self.day_lines:
            if Each_Day.day_type == 'on':
                if Each_Day.booked:
                    count += 1
                    total += 1
                else:
                    total += 1

        if count < total:
            self.booked = False
        else:
            self.booked = True

        # print 'count', count
        # print 'total', total
        #
        #
        # for Each_Day in self.day_lines:
        #     if Each_Day.booked:
        #         count += 1
        # if count < len(self.day_lines):
        #     self.booked = False
        # else:
        #     self.booked = True

    booked = fields.Boolean('Fully Booked', compute='_get_booked', default=False)

    @api.one
    def _get_display_booked(self):
        count = 0
        for Each_Day in self.day_lines:
            if Each_Day.booked:
                count += 1
        if count < len(self.day_lines):
            self.display_booked = str(self.name)
        else:
            self.display_booked = str(self.name) + ' - Fully Booked'

    display_booked = fields.Char(compute='_get_display_booked')
    @api.one
    def _get_month_show(self):
        if self.month == 1:
            self.month_show = 'JAN'
        elif self.month == 2:
            self.month_show = 'FEB'
        elif self.month == 3:
            self.month_show = 'MAR'
        elif self.month == 4:
            self.month_show = 'APR'
        elif self.month == 5:
            self.month_show = 'MAY'
        elif self.month == 6:
            self.month_show = 'JUN'
        elif self.month == 7:
            self.month_show = 'JUL'
        elif self.month == 8:
            self.month_show = 'AUG'
        elif self.month == 9:
            self.month_show = 'SEP'
        elif self.month == 10:
            self.month_show = 'OCT'
        elif self.month == 11:
            self.month_show = 'NOV'
        elif self.month == 12:
            self.month_show = 'DEC'
        else:
            self.month_show = 'None'
    month_show = fields.Char(compute='_get_month_show')




#     day_lines = fields.One2many('salon.month.line', 'month_id')
#
#
# class MonthLines(models.Model):
#     _name = 'salon.month.line'
#
#     days = fields.Many2one('salon.day')
#     month_id = fields.Many2one('salon.month')
#
#     # @api.one
#     # def _get_day_stat(self):
#     #     self.day_stat = self.days.day_type
#     # day_stat = fields.Char(compute='_get_day_stat', string='On/Off')
#
#     day_stat = fields.Selection([('on', 'On'), ('off', 'Off')], default='on')




