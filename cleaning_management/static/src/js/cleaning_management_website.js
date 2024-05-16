/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { useService } from "@web/core/utils/hooks";
    publicWidget.registry.portalDetails = publicWidget.Widget.extend({
        /**
         *  Retrieve all the data from the table.
         */
        selector: '.form',
        events: {
            'change select[name="cleaning_time"]': '_onChangeTime',
            'change input[name="cleaning_date"]': '_onChangeDate',
        },
        /** Super start function to define orm **/
        start: function() {
            this._super.apply(this, arguments);
            this.orm = this.bindService("orm");
        },
        /** Function to retrieve the team corresponding to the cleaning time **/
        _onChangeTime: function() {
            if (!this.$el.find('#cleaning_date').val()) {
                const open_deactivate_modal = true;
                const modalHTML = `
                            <div class="modal ${open_deactivate_modal ? 'show d-block' : ''}" id="popup_error_message" tabindex="-1" role="dialog">
                                <div class="modal-dialog" role="document">
                                    <div class="modal-content">
                                        <div class="modal-header">
                                            <button type="button" class="btn-close" data-dismiss="modal"></button>
                                        </div>
                                        <form class="oe_login_form modal-body" role="form">
                                            Please Choose a Cleaning Date.
                                        </form>
                                    </div>
                                </div>
                            </div>
                        `;
                console.log("$('body')", $("body"))
                $("body").append(modalHTML);
                $("body").find("#popup_error_message").find(".btn-close").on("click", function() {
                    $("body").find("#popup_error_message").remove();
                });
            } else {
                this.$el.find('#cleaning_team_id').empty();
                var self = this;
                this.orm.call('cleaning.management.website', 'get_team_details', [0])
                    .then(function(result) {
                        result.team_list.forEach(element => {
                            var change_time = self.$el.find('#cleaning_time').val();
                            var change_date = self.$el.find('#cleaning_date').val();
                            if (change_time == element.duty) {
                                var domain = [
                                    ['cleaning_date', '=', change_date],
                                    ['cleaning_time', '=', change_time],
                                    ['state', '=', 'draft'],
                                ];
                                self.orm.call('cleaning.team.duty', 'search_read', [domain, ['team_id']])
                                    .then(function(res) {
                                        if (res.length > 0) {
                                            var team_array = [];
                                            res.forEach(e => {
                                                var domain_for_duty = [
                                                    ['cleaning_duty_ids', 'not in', e.id],
                                                    ['id', 'not in', e.team_id[0]],
                                                ];
                                                self.orm.call('cleaning.team', 'search_read', [domain_for_duty, ['id', 'name']]).then(function(res) {
                                                    res.forEach(team => {
                                                        if (!team_array.includes(team.id)) {
                                                            team_array.push(team.id);

                                                            var option = $('<option>').val(team.id).text(team.name);
                                                            self.$el.find('#cleaning_team_id').append(option);
                                                        }
                                                    });
                                                })
                                            })
                                        } else {
                                            var change_time = self.$el.find('#cleaning_time').val();
                                            var domain_for_time = [
                                                ['duty_type', '=', change_time],
                                            ];
                                            self.orm.call('cleaning.team', 'search_read', [domain_for_time, ['id', 'name']]).then(function(res) {
                                                res.forEach(team => {
                                                    var option = $('<option>').val(team.id).text(team.name);
                                                    self.$el.find('#cleaning_team_id').append(option);
                                                })
                                            })
                                        }
                                    });
                            }
                        })
                    });
            }
        },
        _onChangeDate: function() {
            this.$el.find('#cleaning_team_id').empty();
            if (this.$el.find('#cleaning_time').val() != 'null') {
                this.$el.find('#cleaning_time').val("");
            }
        },
    });
