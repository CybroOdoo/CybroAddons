odoo.define('face_recognized_attendance_login.my_attendance', function(require){
"use strict";
/**
 * This file inherit the class MyAttendances, and added the functionality, that
 the login/logout is possible only after the face detection
 */
var core = require('web.core');
var Widget = require('web.Widget');
var rpc = require('web.rpc');
var MyAttendances = require('hr_attendance.my_attendances');
var login = 0
// Login made possible, if and only if the captured image and face of the
// employee matched
MyAttendances.include({
     update_attendance: async function () {
       await rpc.query({
        model:'hr.employee',
        method:'get_login_screen'
    }).then(function (data) {
        login = data
   });
   if (login==1){
          var self = this;
        this._rpc({
                model: 'hr.employee',
                method: 'attendance_manual',
                args: [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances'],
            })
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
   }
   else{
        window.alert("Failed to recognize the face. Please try again....")
   }
     }
});
});
