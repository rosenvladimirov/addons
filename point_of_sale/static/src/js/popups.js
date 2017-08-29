
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

function openerp_pos_popups(instance, module){ //module is instance.point_of_sale
    var QWeb = instance.web.qweb,
    _t = instance.web._t;

    var round_pr = instance.web.round_precision

    module.PopUpWidget = module.PosBaseWidget.extend({
        template: 'PopupWidget',
        init: function(parent, args) {
            this._super(parent, args);
            this.options = {};
        },
        events: {
            'click .button.cancel':  'click_cancel',
            'click .button.confirm': 'click_confirm',
            'click .selection-item': 'click_item',
            'click .input-button':   'click_numpad',
            'click .mode-button':    'click_numpad',
        },
        show: function(){
            if(this.$el){
                this.$el.removeClass('oe_hidden');
            }
        },
        /* called before hide, when a popup is closed */
        close: function(){
        },
        /* hides the popup. keep in mind that this is called in the initialization pass of the 
         * pos instantiation, so you don't want to do anything fancy in here */
        hide: function(){
            if(this.$el){
                this.$el.addClass('oe_hidden');
            }
        },
        // what happens when we click cancel
        // ( it should close the popup and do nothing )
        click_cancel: function(){
            var self = this;
            self.pos_widget.screen_selector.close_popup();
            if (this.options.cancel) {
                this.options.cancel.call(this);
            }
        },
        // what happens when we confirm the action
        click_confirm: function(){
            var self = this;
            self.pos_widget.screen_selector.close_popup();
            if (this.options.confirm) {
                this.options.confirm.call(this);
            }
        },
        // Since Widget does not support extending the events declaration
        // we declared them all in the top class.
        click_item: function(){},
        click_numad: function(){},
    });

    module.ErrorPopupWidget = module.PopUpWidget.extend({
        template:'ErrorPopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this._super();

            $('body').append('<audio src="/point_of_sale/static/src/sounds/error.wav" autoplay="true"></audio>');

            this.message = options.message || _t('Error');
            this.comment = options.comment || '';

            this.renderElement();

            this.pos.barcode_reader.save_callbacks();
            this.pos.barcode_reader.reset_action_callbacks();

            this.$('.footer .button').click(function(){
                self.pos_widget.screen_selector.close_popup();
                if ( options.confirm ) {
                    options.confirm.call(self);
                }
            });
        },
        close:function(){
            this._super();
            this.pos.barcode_reader.restore_callbacks();
        },
    });

    module.ErrorTracebackPopupWidget = module.ErrorPopupWidget.extend({
        template:'ErrorTracebackPopupWidget',
    });

    module.ErrorBarcodePopupWidget = module.ErrorPopupWidget.extend({
        template:'ErrorBarcodePopupWidget',
        show: function(barcode){
            this.barcode = barcode;
            this._super();
        },
    });

    module.ConfirmPopupWidget = module.PopUpWidget.extend({
        template: 'ConfirmPopupWidget',
        show: function(options){
            options = options || {};
            var self = this;
            this._super();

            this.message = options.message || _t('confirm');
            this.comment = options.comment || '';
            this.renderElement();

            this.$('.button.cancel').click(function(){
                self.pos_widget.screen_selector.close_popup();
                if( options.cancel ){
                    options.cancel.call(self);
                }
            });

            this.$('.button.confirm').click(function(){
                self.pos_widget.screen_selector.close_popup();
                if( options.confirm ){
                    options.confirm.call(self);
                }
            });
        },
        close:function(){
            this._super();
        },
    });

    module.ErrorNoClientPopupWidget = module.ErrorPopupWidget.extend({
        template: 'ErrorNoClientPopupWidget',
    });

    module.ErrorInvoiceTransferPopupWidget = module.ErrorPopupWidget.extend({
        template: 'ErrorInvoiceTransferPopupWidget',
    });

    module.UnsentOrdersPopupWidget = module.PopUpWidget.extend({
        template: 'UnsentOrdersPopupWidget',
        show: function(options){
            var self = this;
            this._super(options);
            this.renderElement();
            this.$('.button.confirm').click(function(){
                self.pos_widget.screen_selector.close_popup();
            });
        },
    });

    module.PasswordConfirmPopupWidget = module.PopUpWidget.extend({
        template: 'PasswordConfirmPopupWidget',
        show: function(options){
            var self = this;
            this._super();

            this.message = options.message || '';
            this.renderElement();

            this.$('.button.cancel').click(function(){
                self.pos_widget.screen_selector.close_popup();
                if( options.cancel ){
                    options.cancel.call(self);
                }
            });

            this.$('.button.confirm').click(function(){
                self.button_confirm(options);
            });

            this.$('td.number-char').click(function(e){
                self.numpad_char(this);
            });

            this.$('td.number-clear').click(function(e){
                self.numpad_clear();
            });

                        this.$('td.numpad-backspace').click(function(e){
                                self.numpad_backspace();
                        });

                        self.$('#password_content').focus();
        },
        numpad_backspace: function() {
                var self = this;
                var pass = self.$('#password_content').val();
                        if (pass.length > 0) {
                                self.$('#password_content').val(pass.slice(0, -1));
                        }
                        self.$('#password_content').focus();
        },
        numpad_clear: function() {
                this.$('#password_content').val('').focus();
        },
        numpad_char: function(target) {
                var self = this,
                char = $(target).html(),
                pass = self.$('#password_content').val();

                pass += char;
                self.$('#password_content').val(pass).focus();
        },
        button_confirm: function(options) {
                if (options.confirm) {
                        var self = this,
                pass = self.$('#password_content').val();
                options.confirm.call(self, pass);
            }
        },
    });
    module.SelectVariantPopupWidget = module.PopUpWidget.extend({
        template:'SelectVariantPopupWidget',

        start: function(){
            var self = this;
            // Define Variant Widget
            this.variant_list_widget = new module.VariantListWidget(this,{});
            this.variant_list_widget.replace(this.$('.placeholder-VariantListWidget'));

            // Define Attribute Widget
            this.attribute_list_widget = new module.AttributeListWidget(this,{});
            this.attribute_list_widget.replace(this.$('.placeholder-AttributeListWidget'));

            // Add behaviour on Cancel Button
            this.$('#variant-popup-cancel').off('click').click(function(){
                self.hide();
            });
        },

        show: function(product_tmpl_id){
            var self = this;
            var template = this.pos.db.template_by_id[product_tmpl_id];

            // Display Name of Template
            this.$('#variant-title-name').html(template.name);

            // Render Variants
            var variant_ids  = this.pos.db.template_by_id[product_tmpl_id].product_variant_ids;
            var variant_list = [];
            for (var i = 0, len = variant_ids.length; i < len; i++) {
                variant_list.push(this.pos.db.get_product_by_id(variant_ids[i]));
            }
            this.variant_list_widget.filters = {}
            this.variant_list_widget.set_variant_list(variant_list);

            // Render Attributes
            var attribute_ids  = this.pos.db.attribute_by_template_id(template.id);
            var attribute_list = [];
            for (var i = 0, len = attribute_ids.length; i < len; i++) {
                attribute_list.push(this.pos.db.get_product_attribute_by_id(attribute_ids[i]));
            }
            this.attribute_list_widget.set_attribute_list(attribute_list, template);
            this._super();
        },
    });
}
