
// this file contains the screens definitions. Screens are the
// content of the right pane of the pos, containing the main functionalities. 
// screens are contained in the PosWidget, in pos_widget.js
// all screens are present in the dom at all time, but only one is shown at the
// same time. 
//
// transition between screens is made possible by the use of the screen_selector,
// which is responsible of hiding and showing the screens, as well as maintaining
// the state of the screens between different orders.
//
// all screens inherit from ScreenWidget. the only addition from the base widgets
// are show() and hide() which shows and hides the screen but are also used to 
// bind and unbind actions on widgets and devices. The screen_selector guarantees
// that only one screen is shown at the same time and that show() is called after all
// hide()s

function openerp_pos_errors(instance, module){ //module is instance.point_of_sale
    var QWeb = instance.web.qweb,
    _t = instance.web._t;

    var round_pr = instance.web.round_precision

    module.ErrorsWidget = module.PosBaseWidget.extend({
        init: function(parent, options){
            this._super(parent, options);
            this.set({'last': null,});
            //this.screen_messages = this;
        },

        errors: function(error){
            var self = this;
            var ret = false;
            this.set({'last': null,});

            if(typeof error === 'object'){
                this.set({'last': error['type'],});
                return self.pos_widget.screen_selector.show_popup(error['type'], error['content']);
            } else if(typeof error === 'string') {
                this.set({'last': error,});
                if(error === 'no-lines') {
                    ret = { type: 'error',
                            content: {
                                message: _t('Empty Order'),
                                comment: _t('There must be at least one product in your order before it can be validated'),
                                },
                            }
                } else if (error === 'pricelist-no-active') {
                    ret = { type: 'error',
                            content: {
                                message: _t('Pricelist Error'),
                                comment: _t('At least one pricelist has no active version ! Please create or activate one.'),
                                },
                            }
                } else if (error === 'customer-is-required') {
                    ret = { type: 'error',
                            content: {
                                message: _t('A Customer Name Is Required'),
                                },
                            }
                } else if (error === 'connection-is-down') {
                    ret = { type: 'error',
                            content: {
                                message:_t('Error: Could not Save Changes'),
                                comment:_t('Your Internet connection is probably down.'),
                                },
                            }
                } else if (error === 'unsupported-file-format') {
                    ret = { type: 'error',
                            content: {
                                message:_t('Unsupported File Format'),
                                comment:_t('Only web-compatible Image formats such as .png or .jpeg are supported'),
                                },
                            }
                } else if (error === 'read-image') {
                    ret = { type: 'error',
                            content: {
                                message:_t('Could Not Read Image'),
                                comment:_t('The provided file could not be read due to an unknown error'),
                                },
                            }
                } else if (error === 'not-select-order') {
                    ret = { type: 'error',
                            content: {
                                message: _t('Not select oreder'),
                                comment: _t("Can not validate order, d'not have selected it."),
                                },
                            }
                } else if (error === 'connection-offline') {
                    ret = { type: 'error',
                            content: {
                                message: _t('Connection error'),
                                comment: _t('Can not load the Selected Order because the POS is currently offline'),
                                },
                            }
                } else if (error === 'negative-bank-payment') {
                    ret = { type:    'error',
                            content: {
                                message: _t('Negative Bank Payment'),
                                comment: _t('You cannot have a negative amount in a Bank payment. Use a cash payment method to return money to the customer.'),
                                },
                            }
                } else if (error === 'no-customer-advance') {
                    ret = { type:   'error',
                            content: {
                                message: _t('Found money in/out payment, something is wrong'),
                                comment: _t('You cannot in/out money without selected customer. Please select customer.'),
                                },
                            }
                } else if (error === 'no-rest-without-cash') {
                    ret = { type:    'error',
                            content: {
                                message: _t('Cannot return change without a cash payment method'),
                                comment: _t('There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'),
                                },
                            }
                } else if (error === 'no-advance-payment') {
                    ret = { type:    'error',
                            content: {
                                message: _t("Check: don't found advance payment, something is wrong!"),
                                comment: _t("The order will be returned for clarification if there is a case with a deposit."),
                                },
                            }
                } else if (error === 'anonymous-order') {
                    ret = { type:    'error',
                            content: {
                                message: _t('An anonymous order cannot be invoiced'),
                                comment: _t('Please select a client for this order. This can be done by clicking the order tab'),
                                },
                            }
                } else if (error === 'order-send') {
                    ret = { type:    'error',
                            content: {
                                message: _t('The order could not be sent'),
                                comment: _t('Check your internet connection and try again.'),
                                },
                            }
                }
                if(ret !== false) {
                    return self.pos_widget.screen_selector.show_popup(ret['type'], ret['content']);
                }
            }
            return ret;
        },
        confirms: function(confirm){
            var self = this;
            var ret = false;

            if(typeof error === 'object'){
                return self.pos_widget.screen_selector.show_popup(error['type'], error['content']);
            } else if(typeof error === 'string') {
                if (confirm === 'loan') {
                    console.log("loan", confirm);
                    ret = { type: 'confirm',
                            content: {
                                message: _t("You're sure to give goods on credit ?"),
                                comment: _t("If your confirm, the order be sended on back office to wait payments. Please print The order and save it."),
                                confirm: function(){
                                    console.log("loan ok", error);
                                    return true;
                                    },
                                cancel: function(){
                                    console.log("loan cancel", error);
                                    return false;
                                    },
                                },
                            }
                } else if (confirm === 'deposit') {
                    console.log("deposit", confirm);
                    ret = { type: 'confirm',
                            content: {
                                message: _t("You're sure to give deposit?"),
                                comment: _t("If your confirm, the order be sended on back office to wait final payments. Please print The invoice and save it."),
                                confirm: function(){
                                        return true;
                                    },
                                cancel: function(){
                                        return false;
                                    },
                                },
                            }
                }
                if(ret !== false) {
                    return self.pos_widget.screen_selector.show_popup(ret['type'], ret['content']);
                }
            }
            return ret;
        },
    });
}
