odoo.define('pos_order_question.OrderQuestion', function (require) {
    'use strict';

    // Import necessary modules from the Odoo POS framework
    const Registries = require('point_of_sale.Registries');
    const Orderline = require('point_of_sale.Orderline');
    const OrderWidget = require('point_of_sale.OrderWidget');
    const {Gui} = require('point_of_sale.Gui');

    // Define a new class that extends the existing Orderline class
    const OrderQuestion = (Orderline) =>
        class extends Orderline {
            // Method to add options (questions) related to the product
            AddOptions() {
                // Retrieve order question IDs for the current product
                var ProductQuestions = this.props.line.product.order_question_ids;
                // Retrieve all available order questions from the POS environment
                var OrderQuestions = this.env.pos.order_questions;

                let question = []; // Initialize an array to hold matching questions

                // Loop through each available order question
                for (var i = 0, len = OrderQuestions.length; i < len; i++) {
                    // Loop through each product question associated with the current order line
                    for (var j = 0, leng = ProductQuestions.length; j < leng; j++) {
                        if (OrderQuestions[i].id === ProductQuestions[j]) {
                            question.push(OrderQuestions[i].name);
                        }
                    }
                }
                // Check if any questions were found
                if (question.length !== 0) {
                    // Show a popup with the found questions
                    Gui.showPopup("OrderQuestionPopup", {
                        confirmText: 'Ok',
                        cancelText: 'Cancel',
                        title: 'Extra...',
                        body: question, // Body contains the array of questions
                    });
                } else {
                    // Show a popup indicating that there are no options to select
                    Gui.showPopup("OrderQuestionPopup", {
                        confirmText: 'Ok',
                        cancelText: 'Cancel',
                        title: 'Add Options to Select...',
                    });
                }
            }
        };

    // Extend the Orderline component with the new functionality
    Registries.Component.extend(Orderline, OrderQuestion);
    // Return the OrderWidget (not modified in this code)
    return OrderWidget;
});
