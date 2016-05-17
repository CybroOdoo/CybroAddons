from openerp import models, fields,api,http,SUPERUSER_ID,_
from openerp.osv import fields, osv


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_wait(self, cr, uid, ids, context=None):
        context = context or {}
        for o in self.browse(cr, uid, ids):
            if not any(line.state != 'cancel' for line in o.order_line):
                raise osv.except_osv(_('Error!'),_('You cannot confirm a this booking which has no line.'))
            noprod = self.test_no_product(cr, uid, o, context)
            if (o.order_policy == 'manual') or noprod:
                self.write(cr, uid, [o.id], {'state': 'manual', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
                # =================================================================
                booking_no = o.name
                values = self.get_values_booking(cr, uid, ids, context)[0]
                for Each_Day in values['month'].day_lines:
                    if Each_Day.id == values['day'].id:
                        for Each_Time in Each_Day.period_lines:
                            if Each_Time.id == values['time'].id:
                                for Each_Time_Line in Each_Time.chair_lines:
                                    if Each_Time_Line.chair_id.id == values['chair'].id:
                                        print Each_Day.name, Each_Time.name, Each_Time_Line.chair_id.name
                                        if Each_Time_Line.booked:
                                            raise osv.except_osv(_('Booking Failed !'),_('Mismatch in booking, this chair may be already booked.'))
                                        else:
                                            print 'nooooooooooooo'
                                            cr.execute("UPDATE salon_period_line SET partner_id = %s,book_no = %s where period_id = %s and chair_id = %s", (str(values['partner'].id), booking_no, str(values['time'].id), str(values['chair'].id)))
                # =================================================================
            else:
                self.write(cr, uid, [o.id], {'state': 'progress', 'date_confirm': fields.date.context_today(self, cr, uid, context=context)})
                # =================================================================
                booking_no = o.name
                values = self.get_values_booking(cr, uid, ids, context)[0]
                for Each_Day in values['month'].day_lines:
                    if Each_Day.id == values['day'].id:
                        for Each_Time in Each_Day.period_lines:
                            if Each_Time.id == values['time'].id:
                                for Each_Time_Line in Each_Time.chair_lines:
                                    if Each_Time_Line.chair_id.id == values['chair'].id:
                                        print Each_Day.name, Each_Time.name, Each_Time_Line.chair_id.name
                                        if Each_Time_Line.booked:
                                            raise osv.except_osv(_('Booking Failed !'),_('Mismatch in booking, this chair may be already booked.'))
                                        else:
                                            print 'nooooooooooooo'
                                            cr.execute("UPDATE salon_period_line SET partner_id = %s,book_no = %s where period_id = %s and chair_id = %s", (str(values['partner'].id), booking_no, str(values['time'].id), str(values['chair'].id)))
                # =================================================================
            self.pool.get('sale.order.line').button_confirm(cr, uid, [x.id for x in o.order_line if x.state != 'cancel'])

        return True

    @api.one
    def get_values_booking(self):
        return {'month': self.for_month,
                'day': self.for_day,
                'time': self.for_time,
                'chair': self.char_id,
                'partner': self.partner_id}


    def action_button_confirm(self, cr, uid, ids, context=None):
        # ======================================
        # values = self.get_values_booking(cr, uid, ids, context)[0]
        # cr.execute("UPDATE salon_period_line SET partner_id = %s where period_id = %s and chair_id = %s", (str(values['partner'].id), str(values['time'].id), str(values['chair'].id)))

        # ======================================
        if not context:
            context = {}
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.signal_workflow(cr, uid, ids, 'order_confirm')
        if context.get('send_email'):
            self.force_quotation_send(cr, uid, ids, context=context)
        return True



