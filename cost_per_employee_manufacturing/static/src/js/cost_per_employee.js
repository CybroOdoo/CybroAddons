odoo.define('cost_per_employee_manufacturing.cost_per_employee', function (require) {
    'use strict';

    var rpc = require('web.rpc');
    function computeCostPerEmployee() {
    /**
        *Create function for compute cost per employee
    */
        rpc.query({
            model: 'mrp.production',
            method: '_compute_cost_per_hour',
            args: [[]],
        }).then(function (result) {
            var costPerEmployee = result.toFixed(2);
            // Compute the cost per employee and format the value
            $('#cost_per_employee').text(costPerEmployee);
            // Update the value inside the template
        });
    }
        computeCostPerEmployee();
});
