odoo.define('pos_face_recognition.pos_face_recognition', function (require) {
    'use strict';
    const LoginScreen = require('pos_hr.LoginScreen');
    const Registries = require('point_of_sale.Registries');
    const SelectCashierMixin = require('pos_hr.SelectCashierMixin');
    const rpc = require('web.rpc');
    const FaceRecognition = (LoginScreen) =>
    class extends LoginScreen {
    /**
    For camera open
    **/
        async cameraOpen(employee) {
        var self= this
             await rpc.query({
                    model:'hr.employee',
                    method:'camera_open',
                    args: [employee]
            }).then( function(data){
             if (data == 1) {
                self.env.pos.set_cashier(employee);
                self.props.resolve({ confirmed: true, payload: true });
                self.trigger('close-temp-screen');
            } else {
                self.showPopup('ErrorPopup',{
                          'title': "Unauthorized Access detected",
                          'body': "Face Recognition Failed",
                     });
                return;
            }
           });
        }
       /**
        For selecting the cashier
        **/
         async selectCashier() {
         if (this.env.pos.config.module_pos_hr) {
                const employeesList = this.env.pos.employees
                    .filter((employee) => employee.id !==
                    this.env.pos.get_cashier().id).map((employee) => {
                        return {
                            id: employee.id,
                            item: employee,
                            label: employee.name,
                            isSelected: false,
                        };
                    });
                let {confirmed, payload: employee} =
                await this.showPopup('SelectionPopup', {
                    title: this.env._t('Change Cashier'),
                    list: employeesList,
                });
                if (!confirmed) {
                    return;
                }
                if (employee) {
                    employee = await this.cameraOpen(employee);
                }
                return employee;
            }
         }
    }
    Registries.Component.extend(LoginScreen, FaceRecognition);
    return FaceRecognition;
});
