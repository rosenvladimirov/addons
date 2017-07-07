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

            var inx = _.findIndex(_super_PosModel.prototype.models,function(model){ return model.model === 'pos.config'; })
            _super_PosModel.prototype.models[inx] = {
                model: 'pos.config',
                fields: pos_config_model.fields,
                domain: function(self){ return [['id','=', self.pos_session.config_id[0]]]; },
                loaded: function(self,configs){
                    self.config = configs[0];
                    self.config.use_proxy = self.config.iface_payment_terminal ||
                                            self.config.iface_electronic_scale ||
                                            self.config.iface_print_via_proxy  ||
                                            self.config.iface_fprint_via_proxy ||
                                            self.config.iface_scan_via_proxy   ||
                                            self.config.iface_cashdrawer;

                    self.barcode_reader.add_barcode_patterns({
                        'product':  self.config.barcode_product,
                        'cashier':  self.config.barcode_cashier,
                        'client':   self.config.barcode_customer,
                        'weight':   self.config.barcode_weight,
                        'discount': self.config.barcode_discount,
                        'price':    self.config.barcode_price,
                    });

                    if (self.config.company_id[0] !== self.user.company_id[0]) {
                        throw new Error(_t("Error: The Point of Sale User must belong to the same company as the Point of Sale. You are probably trying to load the point of sale as an administrator in a multi-company setup, with the administrator account set to the wrong company."));
                    }
                },
            },
