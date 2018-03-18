/*
    POS Datecs Fiscal Printer module for Odoo
    Copyright (C) 2017 Rosen Vladimirov
    @author: Rosen Vladimirov
    The licence is in the file __openerp__.py
*/

openerp.pos_datecs = function(instance){
    module = instance.point_of_sale;

    module.ProxyDevice = module.ProxyDevice.extend({
        payment_terminal_transaction_start: function(line, currency_iso){
            var data = {'amount' : line.get_amount(),
                        'currency_iso' : currency_iso,
                        'payment_mode' : line.cashregister.journal.payment_mode};
            this.message('payment_terminal_transaction_start', {'payment_info' : JSON.stringify(data)});
        },
    });

    module.PaymentScreenWidget.include({
        render_paymentline: function(line){
            el_node = this._super(line);
            var self = this;
            if (line.cashregister.journal.payment_mode && this.pos.config.iface_payment_terminal){
                el_node.querySelector('.payment-terminal-transaction-start')
                    .addEventListener('click', function(){self.pos.proxy.payment_terminal_transaction_start(line, self.pos.currency.name)});
                }
            return el_node;
        },
    });

};
