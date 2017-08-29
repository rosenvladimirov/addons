function openerp_pos_widgets(instance, module){ //module is instance.point_of_sale
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    var round_pr = instance.web.round_precision;
    var round_di = instance.web.round_decimals;

    module.DomCache = instance.web.Class.extend({
        init: function(options){
            options = options || {};
            this.max_size = options.max_size || 2000;

            this.cache = {};
            this.access_time = {};
            this.size = 0;
        },
        cache_node: function(key,node){
            var cached = this.cache[key];
            this.cache[key] = node;
            this.access_time[key] = new Date().getTime();
            if(!cached){
                this.size++;
                while(this.size >= this.max_size){
                    var oldest_key = null;
                    var oldest_time = new Date().getTime();
                    for(var key in this.cache){
                        var time = this.access_time[key];
                        if(time <= oldest_time){
                            oldest_time = time;
                            oldest_key  = key;
                        }
                    }
                    if(oldest_key){
                        delete this.cache[oldest_key];
                        delete this.access_time[oldest_key];
                    }
                    this.size--;
                }
            }
            return node;
        },
        get_node: function(key){
            var cached = this.cache[key];
            if(cached){
                this.access_time[key] = new Date().getTime();
            }
            return cached;
        },
    });

    module.OnscreenControlbuttonsWidget = module.PosBaseWidget.extend({
        template: 'OnscreenControlButons',
        init: function(parent, options) {
            this._super(parent);
            var self = this;
        },
    });

    module.PayKeypadWidget = module.PosBaseWidget.extend({
        template:'PayKeypadWidget',
        init: function(parent, options) {
            this._super(parent);
            this.state = new module.NumpadState();
            window.numpadstate = this.state;
            var self = this;
        },
        start: function() {
            this.$el.find('.numpad-backspace').click(_.bind(this.clickDeleteLastChar, this));
            this.$el.find('.number-char').click(_.bind(this.clickAppendNewChar, this));
            this.$el.find('.decimal-char').click(_.bind(this.clickAppendNewDecimalChar, this));
        },
        clickDeleteLastChar: function() {
            return this.state.deleteLastChar();
        },
        clickSwitchSign: function() {
            return this.state.switchSign();
        },
        clickAppendNewChar: function(event) {
            var newChar;
            newChar = event.currentTarget.innerText || event.currentTarget.textContent;
            return this.state.appendNewChar(newChar);
        },
        clickAppendNewDecimalChar: function(event) {
            var newChar;
            newChar = event.currentTarget.innerText || event.currentTarget.textContent;
            return this.state.appendNewChar(newChar);
        },

    });

    module.NumpadWidget = module.PosBaseWidget.extend({
        template:'NumpadWidget',
        init: function(parent, options) {
            this._super(parent);
            this.state = new module.NumpadState();
            window.numpadstate = this.state;
            var self = this;
        },
        start: function() {
            this.state.bind('change:mode', this.changedMode, this);
            this.changedMode();
            this.$el.find('.numpad-backspace').click(_.bind(this.clickDeleteLastChar, this));
            this.$el.find('.numpad-minus').click(_.bind(this.clickSwitchSign, this));
            this.$el.find('.number-char').click(_.bind(this.clickAppendNewChar, this));
            this.$el.find('.mode-button').click(_.bind(this.clickChangeMode, this));
        },
        clickDeleteLastChar: function() {
            return this.state.deleteLastChar();
        },
        clickSwitchSign: function() {
            return this.state.switchSign();
        },
        clickAppendNewChar: function(event) {
            var newChar;
            newChar = event.currentTarget.innerText || event.currentTarget.textContent;
            return this.state.appendNewChar(newChar);
        },
        clickChangeMode: function(event) {
            var newMode = event.currentTarget.attributes['data-mode'].nodeValue;
            return this.state.changeMode(newMode);
        },
        changedMode: function() {
            var mode = this.state.get('mode');
            $('.selected-mode').removeClass('selected-mode');
            $(_.str.sprintf('.mode-button[data-mode="%s"]', mode), this.$el).addClass('selected-mode');
        },
    });

    // The paypad allows to select the payment method (cashregisters) 
    // used to pay the order.
    module.PaypadWidget = module.PosBaseWidget.extend({
        template: 'PaypadWidget',
        renderElement: function() {
            var self = this;
            this._super();

            _.each(this.pos.cashregisters,function(cashregister) {
                var button = new module.PaypadButtonWidget(self,{
                    pos: self.pos,
                    pos_widget : self.pos_widget,
                    cashregister: cashregister,
                });
                button.appendTo(self.$el);
            });
        }
    });

    module.PaypadButtonWidget = module.PosBaseWidget.extend({
        template: 'PaypadButtonWidget',
        init: function(parent, options){
            this._super(parent, options);
            this.cashregister = options.cashregister;
        },
        renderElement: function() {
            var self = this;
            this._super();

            this.$el.click(function(){
                if (self.pos.get('selectedOrder').get('screen') === 'receipt'){  //TODO Why ?
                    console.warn('TODO should not get there...?');
                    return;
                }
                self.pos.get('selectedOrder').addPaymentline(self.cashregister);
                self.pos_widget.screen_selector.set_current_screen('payment');
            });
        },
    });

    module.OrderWidget = module.PosBaseWidget.extend({
        template:'OrderWidget',
        init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.editable = false;
            this.pos.bind('change:selectedOrder', this.change_selected_order, this);
            this.line_click_handler = function(event){
                if(!self.editable){
                    return;
                }
                self.pos.get('selectedOrder').selectLine(this.orderline);
                self.pos_widget.numpad.state.reset();
            };
            this.client_change_handler = function(event){
                self.update_summary();
            }
            this.bind_order_events();
        },
        enable_numpad: function(){
            this.disable_numpad();  //ensure we don't register the callbacks twice
            this.numpad_state = this.pos_widget.numpad.state;
            if(this.numpad_state){
                this.numpad_state.reset();
                this.numpad_state.bind('set_value',   this.set_value, this);
            }

        },
        disable_numpad: function(){
            if(this.numpad_state){
                this.numpad_state.unbind('set_value',  this.set_value);
                this.numpad_state.reset();
            }
        },
        set_editable: function(editable){
            this.editable = editable;
            if(editable){
                this.enable_numpad();
            }else{
                this.disable_numpad();
                this.pos.get('selectedOrder').deselectLine();
            }
        },
        set_value: function(val) {
            var order = this.pos.get('selectedOrder');
            if (this.editable && order.getSelectedLine()) {
                var mode = this.numpad_state.get('mode');
                if( mode === 'quantity'){
                    order.getSelectedLine().set_quantity(val);
                }else if( mode === 'discount'){
                    order.getSelectedLine().set_discount(val);
                }else if( mode === 'price'){
                    //console.log("Set value", val)
                    order.getSelectedLine().set_manual_price(true);
                    order.getSelectedLine().set_unit_price({price: val, tax_included: true,});
                }
            }
        },
        change_selected_order: function() {
            this.bind_order_events();
            this.renderElement();
        },
        bind_order_events: function() {

            var order = this.pos.get('selectedOrder');
                order.unbind('change:client', this.client_change_handler);
                order.bind('change:client', this.client_change_handler);

            var lines = order.get('orderLines');
                lines.unbind();
                lines.bind('add', function(){ 
                        this.numpad_state.reset();
                        this.renderElement(true);
                    },this);
                lines.bind('remove', function(line){
                        this.remove_orderline(line);
                        this.numpad_state.reset();
                        this.update_summary();
                    },this);
                lines.bind('change', function(line){
                        this.rerender_orderline(line);
                        this.update_summary();
                    },this);
        },
        render_orderline: function(orderline){
            var el_str  = openerp.qweb.render('Orderline',{widget:this, line:orderline}); 
            var el_node = document.createElement('div');
                el_node.innerHTML = _.str.trim(el_str);
                el_node = el_node.childNodes[0];
                el_node.orderline = orderline;
                el_node.addEventListener('click',this.line_click_handler);

            orderline.node = el_node;
            return el_node;
        },
        remove_orderline: function(order_line){
            if(this.pos.get('selectedOrder').get('orderLines').length === 0){
                this.renderElement();
            }else{
                order_line.node.parentNode.removeChild(order_line.node);
            }
        },
        rerender_orderline: function(order_line){
            var node = order_line.node;
            var replacement_line = this.render_orderline(order_line);
            node.parentNode.replaceChild(replacement_line,node);
        },
        // overriding the openerp framework replace method for performance reasons
        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },
        renderElement: function(scrollbottom){
            this.pos_widget.numpad.state.reset();

            var order  = this.pos.get('selectedOrder');
            var orderlines = order.get('orderLines').models;

            var el_str  = openerp.qweb.render('OrderWidget',{widget:this, order:order, orderlines:orderlines});

            var el_node = document.createElement('div');
                el_node.innerHTML = _.str.trim(el_str);
                el_node = el_node.childNodes[0];


            var list_container = el_node.querySelector('.orderlines');
            for(var i = 0, len = orderlines.length; i < len; i++){
                var orderline = this.render_orderline(orderlines[i]);
                list_container.appendChild(orderline);
            }

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;
            this.update_summary();

            if(scrollbottom){
                this.el.querySelector('.order-scroller').scrollTop = 100 * orderlines.length;
            }
            if (orderlines.length === 0) {
                $(this.pos_widget.el).find('.save-button').addClass('oe_hidden');
                $(this.pos_widget.el).find('.load-button').removeClass('oe_hidden');
            }
            if (orderlines.length > 0) {
                $(this.pos_widget.el).find('.load-button').addClass('oe_hidden');
                $(this.pos_widget.el).find('.save-button').removeClass('oe_hidden');
            }
        },
        update_summary: function(){
            var order = this.pos.get('selectedOrder');
            var total     = order ? order.getTotalTaxIncluded() : 0;
            var taxes     = order ? total - order.getTotalTaxExcluded() : 0;
            var advance   = order ? order.getPaidAdvance() : 0;
            var dueLeft   = order ? order.getDueLeft() : 0;

            this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
            this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);
            this.el.querySelector('.summary .total .subadvance .value').textContent = this.format_currency(advance);
            this.el.querySelector('.summary .total .subpayment .value').textContent = this.format_currency(dueLeft);

        },
    });

    module.OrderButtonWidget = module.PosBaseWidget.extend({
        template:'OrderButtonWidget',
        init: function(parent, options) {
            this._super(parent,options);
            var self = this;

            this.order = options.order;
            this.order.bind('destroy',this.destroy, this );
            this.order.bind('change', this.renderElement, this );
            this.pos.bind('change:selectedOrder', this.renderElement,this );
        },
        renderElement:function(){
            this.selected = ( this.pos.get('selectedOrder') === this.order )
            this._super();
            var self = this;
            this.$el.click(function(){ 
                if( self.pos.get('selectedOrder') === self.order ){
                    var ss = self.pos.pos_widget.screen_selector;
                    if(ss.get_current_screen() === 'clientlist'){
                        ss.back();
                    }else if (ss.get_current_screen() !== 'receipt'){
                        ss.set_current_screen('clientlist');
                    }
                }else{
                    self.selectOrder();
                }
            });
            if( this.selected){
                this.$el.addClass('selected');
            }
        },
        selectOrder: function(event) {
            this.pos.set({selectedOrder: this.order});
            this.pos.pricelist_engine.update_products_ui(this.order.get_client() || false);
        },
        destroy: function(){
            this.order.unbind('destroy', this.destroy, this);
            this.order.unbind('change',  this.renderElement, this);
            this.pos.unbind('change:selectedOrder', this.renderElement, this);
            this._super();
        },
    });

    module.ActionButtonWidget = instance.web.Widget.extend({
        template:'ActionButtonWidget',
        icon_template:'ActionButtonWidgetWithIcon',
        init: function(parent, options){
            this._super(parent, options);
            this.label = options.label || 'button';
            this.rightalign = options.rightalign || false;
            this.click_action = options.click;
            this.disabled = options.disabled || false;
            if(options.icon){
                this.icon = options.icon;
                this.template = this.icon_template;
            }
        },
        set_disabled: function(disabled){
            if(this.disabled != disabled){
                this.disabled = !!disabled;
                this.renderElement();
            }
        },
        renderElement: function(){
            this._super();
            if(this.click_action && !this.disabled){
                this.$el.click(_.bind(this.click_action, this));
            }
        },
    });

    module.ActionBarWidget = instance.web.Widget.extend({
        template:'ActionBarWidget',
        init: function(parent, options){
            this._super(parent,options);
            this.button_list = [];
            this.buttons = {};
            this.visibility = {};
        },
        set_element_visible: function(element, visible, action){
            if(visible != this.visibility[element]){
                this.visibility[element] = !!visible;
                if(visible){
                    this.$('.'+element).removeClass('oe_hidden');
                }else{
                    this.$('.'+element).addClass('oe_hidden');
                }
            }
            if(visible && action){
                this.action[element] = action;
                this.$('.'+element).off('click').click(action);
            }
        },
        set_button_disabled: function(name, disabled){
            var b = this.buttons[name];
            if(b){
                b.set_disabled(disabled);
            }
        },
        destroy_buttons:function(){
            for(var i = 0; i < this.button_list.length; i++){
                this.button_list[i].destroy();
            }
            this.button_list = [];
            this.buttons = {};
            return this;
        },
        get_button_count: function(){
            return this.button_list.length;
        },
        add_new_button: function(button_options){
            var button = new module.ActionButtonWidget(this,button_options);
            this.button_list.push(button);
            if(button_options.name){
                this.buttons[button_options.name] = button;
            }
            button.appendTo(this.$('.pos-actionbar-button-list'));
            return button;
        },
        show:function(){
            this.$el.removeClass('oe_hidden');
        },
        hide:function(){
            this.$el.addClass('oe_hidden');
        },
    });

    module.ProductCategoriesWidget = module.PosBaseWidget.extend({
        template: 'ProductCategoriesWidget',
        init: function(parent, options){
            var self = this;
            this._super(parent,options);
            this.product_type = options.product_type || 'all';  // 'all' | 'weightable'
            this.onlyWeightable = options.onlyWeightable || false;
            this.category = this.pos.root_category;
            this.breadcrumb = [];
            this.subcategories = [];
            this.product_list_widget = options.product_list_widget || null;
            this.category_cache = new module.DomCache();
            this.set_category();

            this.switch_category_handler = function(event){
                self.set_category(self.pos.db.get_category_by_id(Number(this.dataset['categoryId'])));
                self.renderElement();
            };

            this.clear_search_handler = function(event){
                self.clear_search();
            };

            var search_timeout  = null;
            this.search_handler = function(event){
                clearTimeout(search_timeout);

                var query = this.value;

                search_timeout = setTimeout(function(){
                    self.perform_search(self.category, query, event.which === 13);
                },70);
            };
        },

        // changes the category. if undefined, sets to root category
        set_category : function(category){
            var db = this.pos.db;
            if(!category){
                this.category = db.get_category_by_id(db.root_category_id);
            }else{
                this.category = category;
            }
            this.breadcrumb = [];
            var ancestors_ids = db.get_category_ancestors_ids(this.category.id);
            for(var i = 1; i < ancestors_ids.length; i++){
                this.breadcrumb.push(db.get_category_by_id(ancestors_ids[i]));
            }
            if(this.category.id !== db.root_category_id){
                this.breadcrumb.push(this.category);
            }
            this.subcategories = db.get_category_by_id(db.get_category_childs_ids(this.category.id));
        },

        get_image_url: function(category){
            return window.location.origin + '/web/binary/image?model=pos.category&field=image_medium&id='+category.id;
        },

        render_category: function( category, with_image ){
            var cached = this.category_cache.get_node(category.id);
            if(!cached){
                if(with_image){
                    var image_url = this.get_image_url(category);
                    var category_html = QWeb.render('CategoryButton',{ 
                            widget:  this, 
                            category: category, 
                            image_url: this.get_image_url(category),
                        });
                        category_html = _.str.trim(category_html);
                    var category_node = document.createElement('div');
                        category_node.innerHTML = category_html;
                        category_node = category_node.childNodes[0];
                }else{
                    var category_html = QWeb.render('CategorySimpleButton',{ 
                            widget:  this, 
                            category: category, 
                        });
                        category_html = _.str.trim(category_html);
                    var category_node = document.createElement('div');
                        category_node.innerHTML = category_html;
                        category_node = category_node.childNodes[0];
                }
                this.category_cache.cache_node(category.id,category_node);
                return category_node;
            }
            return cached; 
        },

        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },

        renderElement: function(){
            var self = this;

            var el_str  = openerp.qweb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
                el_node.innerHTML = el_str;
                el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }

            this.el = el_node;

            var hasimages = false;  //if none of the subcategories have images, we don't display buttons with icons
            for(var i = 0; i < this.subcategories.length; i++){
                if(this.subcategories[i].image){
                    hasimages = true;
                    break;
                }
            }

            var list_container = el_node.querySelector('.category-list');
            if (list_container) { 
                if (!hasimages) {
                    list_container.classList.add('simple');
                } else {
                    list_container.classList.remove('simple');
                }
                for(var i = 0, len = this.subcategories.length; i < len; i++){
                    list_container.appendChild(this.render_category(this.subcategories[i],hasimages));
                };
            }

            var buttons = el_node.querySelectorAll('.js-category-switch');
            for(var i = 0; i < buttons.length; i++){
                buttons[i].addEventListener('click',this.switch_category_handler);
            }

            var products = this.pos.db.get_product_by_category(this.category.id);
            this.product_list_widget.set_product_list(products);

            this.el.querySelector('.searchbox input').addEventListener('keyup',this.search_handler);
            $('.searchbox input', this.el).keypress(function(e){
                e.stopPropagation();
            });

            this.el.querySelector('.search-clear').addEventListener('click',this.clear_search_handler);

            if(this.pos.config.iface_vkeyboard && this.pos_widget.onscreen_keyboard){
                this.pos_widget.onscreen_keyboard.connect($(this.el.querySelector('.searchbox input')));
            }
        },

        // resets the current category to the root category
        reset_category: function(){
            this.set_category();
            this.renderElement();
        },

        // empties the content of the search box
        clear_search: function(){
            var products = this.pos.db.get_product_by_category(this.category.id);
            this.product_list_widget.set_product_list(products);
            var input = this.el.querySelector('.searchbox input');
                input.value = '';
                input.focus();
        },
        perform_search: function(category, query, buy_result){
            if(query){
                var products = this.pos.db.search_product_in_category(category.id,query)
                if(buy_result && products.length === 1){
                        var selectOrder = this.pos.get('selectedOrder');
                        selectOrder.addProduct(products[0], this.pos.pricelist_engine.update_products_prices(products[0], selectOrder.get_client()));
                        this.clear_search();
                }else{
                    this.product_list_widget.set_product_list(products);
                }
            }else{
                var products = this.pos.db.get_product_by_category(this.category.id);
                this.product_list_widget.set_product_list(products);
            }
        },

    });

    module.ProductListInfoWidget = module.PosBaseWidget.extend({
        template: 'ProductListInfoWidget',
        init: function(parent, options){
            options = options || {};
            this._super(parent, options);
            this.info = _.isEmpty(options.info) ? '' : options.info;
        },
        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },
        renderElement: function(){
            var self = this;
            this._super();
            var info_html = QWeb.render(this.template,{ 
                    widget:  this, 
                    name: this.info, 
                    info: this.moreinfo,
                });
            info_html = _.str.trim(info_html);
            var info_node = document.createElement('div');
            info_node.innerHTML = info_html;
            info_node = info_node.childNodes[0];
            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(info_node,this.el);
            }

        },
        show: function(options){
            options = options || {};
            this._super(options);
            this.info = _.isEmpty(options.info) ? '' : options.info;
            this.moreinfo = _.isEmpty(options.addinfo) ? '' : options.addinfo;
            this.renderElement();
            this.$el.removeClass('oe_hidden'); 
        },
        hide: function(){ this.$el.addClass('oe_hidden'); },
    });

    module.ProductListWidget = module.PosBaseWidget.extend({
        template:'ProductListWidget',
        init: function(parent, options) {
            var self = this;
            this._super(parent,options);
            this.model = options.model;
            this.productwidgets = [];
            this.weight = options.weight || 0;
            this.show_scale = options.show_scale || false;
            this.next_screen = options.next_screen || false;
            console.log("Prouctslist", options);
            this.click_product_handler = function(event){
                var product = self.pos.db.get_product_by_id(this.dataset['productId']);
                if (product.product_variant_count == 1) {
                    // Normal behaviour, The template has only one variant
                    options.click_product_action(product);
                } else {
                    // Display for selection all the variants of a template
                    self.pos.pos_widget.screen_selector.show_popup('select-variant-popup', product.product_tmpl_id);
                }
            };
            this.product_list = options.product_list || [];
            this.product_cache = new module.DomCache();
        },
        set_product_list: function(product_list){
            this.product_list = product_list;
            for (var i = this.product_list.length - 1; i >= 0; i--){
                if (!this.product_list[i].is_primary_variant){
                    this.product_list.splice(i, 1);
                }
            }
            this.renderElement();
        },
        set_custom_header: function(header, more){
            if(!_.isEmpty(this.product_info_widget)){
                this.product_info_widget.show({info: header, addinfo: more});
            }
        },
        get_product_image_url: function(product){
            return window.location.origin + '/web/binary/image?model=product.product&field=image_medium&id='+product.id;
        },
        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },
        render_product: function(product,partner,hasFilter){
            var cached = this.product_cache.get_node(product.id);
            if(!cached){
                //var lst_price = round_di(product.lst_price || 0, this.pos.dp['Product Price']);
                var price = this.pos.pricelist_engine.update_products_prices(product, partner, this.pos.db);
                var image_url = this.get_product_image_url(product);

                if(hasFilter){
                    var lst_price = this.pos_widget.format_currency(price.lst_price, 'Product Price');
                    var display_price = this.pos_widget.format_currency(price.price, 'Product Price');
                    var order_price = this.pos.taxes_engine.get_all_prices({quantity: 1, unit_price: product.order_price, disc: 0, force_tax_included: false, product: product,}).priceWithTax;
                    price = {lst_price: price.lst_price, price: order_price, tooltip: "("+lst_price+"/"+display_price+")", discount: (Math.abs(price.price - order_price) > 0.001)};
                }
                //console.log("Prices", price, hasFilter, product.max_qty);
                if (product.product_variant_count == 1){
                    var product_html = QWeb.render('Product',{ 
                            widget:  this, 
                            product: product, 
                            image_url: this.get_product_image_url(product),
                            price: price,
                            max_qty: hasFilter ? product.max_qty : '',
                        });
                } else {
                    var product_html = QWeb.render('Template',{ 
                            widget:  this, 
                            product: product, 
                            image_url: this.get_product_image_url(product),
                        });
                }
                var product_node = document.createElement('div');
                product_node.innerHTML = product_html;
                product_node = product_node.childNodes[1];
                this.product_cache.cache_node(product.id,product_node);
                return product_node;
            }
            return cached;
        },
        renderElement: function() {
            var self = this;
            var selectOrder = this.pos.get('selectedOrder');
            var partner = selectOrder.get_client();
            var hasFilter = selectOrder.get_product_filter().length !== 0;
            // this._super()
            var el_str  = openerp.qweb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
                el_node.innerHTML = el_str;
                el_node = el_node.childNodes[1];

            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;
            //console.log("products", this.product_list);
            var list_container = el_node.querySelector('.product-list');
            for(var i = 0, len = this.product_list.length; i < len; i++){
                var product_node = this.render_product(this.product_list[i],partner,hasFilter);
                product_node.addEventListener('click',this.click_product_handler);
                list_container.appendChild(product_node);
            };
        },
        /*
        update_products_price: function(partner) {
            var self = this;
            var product_list_ui = self.$('.product-list span.product');
            for (var i = 0, len = product_list_ui.length; i < len; i++) {
                var product_ui = product_list_ui[i];
                var product_id = $(product_ui).data('product-id');
                var product = $.extend({}, db.get_product_by_id(product_id));
                var price = this.pos.pricelist_engine.update_products_prices(product, partner, this.pos.db);
                $(product_ui).find('.price-tag').html(price.price);
                if (price.tooltip != '') {
                    $(product_ui).find('.price-tag').attr(
                        'data-original-title', price.tooltip
                    );
                    $(product_ui).find('.price-tag').attr(
                        'data-toggle', 'tooltip'
                    );
                    $(product_ui).find('.price-tag').tooltip(
                        {delay: {show: 50, hide: 100}}
                    );
                }
            }
        },
        */
    });
    /* ********************************************************
    Define: pos_product_template.VariantListWidget

    - This widget will display a list of Variants;
    - This widget has some part of code that come from point_of_sale.ProductListWidget;
    *********************************************************** */
    module.VariantListWidget = module.PosBaseWidget.extend({
        template:'VariantListWidget',

        init: function(parent, options) {
            var self = this;
            this._super(parent, options);
            this.variant_list = [];
            this.filter_variant_list = [];
            this.filters = {};
            this.click_variant_handler = function(event){
                var variant = self.pos.db.get_product_by_id(this.dataset['variantId']);
                if(variant.to_weight && self.pos.config.iface_electronic_scale){
                    self.__parentedParent.hide();
                    self.pos_widget.screen_selector.set_current_screen('scale',{product: variant});
                }else{
                    self.__parentedParent.hide();
                    var selectOrder = self.pos.get('selectedOrder');
                    selectOrder.addProduct(variant, this.pos.pricelist_engine.update_products_prices(variant, selectOrder.get_client()));
                }
            };
        },

        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },

        set_filter: function(attribute_id, value_id){
            this.filters[attribute_id] = value_id;
            this.filter_variant();
        },

        reset_filter: function(attribute_id){
            if (attribute_id in this.filters){
                delete this.filters[attribute_id];
            }
            this.filter_variant();
        },

        filter_variant: function(){
            value_list = []
            for (var item in this.filters){
                value_list.push(parseInt(this.filters[item]));
            }
            this.filter_variant_list = [];
            for (index in this.variant_list){
                variant = this.variant_list[index];
                found = true;
                for (var i = 0; i < value_list.length; i++){
                    found = found && (variant.attribute_value_ids.indexOf(value_list[i]) != -1);
                }
                if (found){
                    this.filter_variant_list.push(variant);
                }
            }
            this.renderElement();
        },

        set_variant_list: function(variant_list){
            this.variant_list = variant_list;
            this.filter_variant_list = variant_list;
            this.renderElement();
        },

        render_variant: function(variant){
            var variant_html = QWeb.render('VariantWidget', {
                    widget:  this,
                    variant: variant,
                });
            var variant_node = document.createElement('div');
            variant_node.innerHTML = variant_html;
            variant_node = variant_node.childNodes[1];
            return variant_node;
        },

        renderElement: function() {
            var self = this;
            var el_html  = openerp.qweb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
            el_node.innerHTML = el_html;
            el_node = el_node.childNodes[1];
            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;
            var list_container = el_node.querySelector('.variant-list');
            for(var i = 0, len = this.filter_variant_list.length; i < len; i++){
                var variant_node = this.render_variant(this.filter_variant_list[i]);
                variant_node.addEventListener('click',this.click_variant_handler);
                list_container.appendChild(variant_node);
            }
        },

    });

    /* ********************************************************
    Define: pos_product_template.AttributeListWidget

        - This widget will display a list of Attribute;
    *********************************************************** */
    module.AttributeListWidget = module.PosBaseWidget.extend({
        template:'AttributeListWidget',

        init: function(parent, options) {
            var self = this;
            this.attribute_list = [];
            this.product_template = null;
            this.click_set_attribute_handler = function(event){
                /*TODO: Refactor this function with elegant DOM manipulation */
                // remove selected item
                parent = this.parentElement.parentElement.parentElement;
                parent.children[0].classList.remove('selected');
                for (var i = 0 ; i < parent.children[1].children[0].children.length; i ++){
                    elem = parent.children[1].children[0].children[i];
                    elem.children[0].classList.remove('selected');
                }
                // add selected item
                this.children[0].classList.add('selected');
                self.__parentedParent.variant_list_widget.set_filter(this.dataset['attributeId'], this.dataset['attributeValueId']);
            };
            this.click_reset_attribute_handler = function(event){
                /*TODO: Refactor this function with elegant DOM manipulation */
                // remove selected item
                parent = this.parentElement;
                parent.children[0].classList.remove('selected');
                for (var i = 0 ; i < parent.children[1].children[0].children.length; i ++){
                    elem = parent.children[1].children[0].children[i];
                    elem.children[0].classList.remove('selected');
                }
                // add selected item
                this.classList.add('selected');
                self.__parentedParent.variant_list_widget.reset_filter(this.dataset['attributeId']);
            };
            this._super(parent, options);
        },

        replace: function($target){
            this.renderElement();
            var target = $target[0];
            target.parentNode.replaceChild(this.el,target);
        },

        set_attribute_list: function(attribute_list, product_template){
            this.attribute_list = attribute_list;
            this.product_template = product_template;
            this.renderElement();
        },

        render_attribute: function(attribute){
            var attribute_html = QWeb.render('AttributeWidget',{
                    widget:  this,
                    attribute: attribute,
                });
            var attribute_node = document.createElement('div');
            attribute_node.innerHTML = attribute_html;
            attribute_node = attribute_node.childNodes[1];

            var list_container = attribute_node.querySelector('.value-list');
            for(var i = 0, len = attribute.value_ids.length; i < len; i++){
                var value = this.pos.db.get_product_attribute_value_by_id(attribute.value_ids[i]);
                var product_list = this.pos.db.get_product_by_ids(this.product_template.product_variant_ids);
                var subproduct_list = this.pos.db.get_product_by_value_and_products(value.id, product_list);
                var variant_qty = subproduct_list.length;
                // Hide product attribute value if there is no product associated to it
                if (variant_qty != 0) {
                    var value_node = this.render_value(value, variant_qty);
                    value_node.addEventListener('click', this.click_set_attribute_handler);
                    list_container.appendChild(value_node);
                }
            };
            return attribute_node;
        },

        render_value: function(value, variant_qty){
            var value_html = QWeb.render('AttributeValueWidget',{
                    widget:  this,
                    value: value,
                    variant_qty: variant_qty,
                });
            var value_node = document.createElement('div');
            value_node.innerHTML = value_html;
            value_node = value_node.childNodes[1];
            return value_node;
        },


        renderElement: function() {
            var self = this;
            var el_html  = openerp.qweb.render(this.template, {widget: this});
            var el_node = document.createElement('div');
            el_node.innerHTML = el_html;
            el_node = el_node.childNodes[1];
            if(this.el && this.el.parentNode){
                this.el.parentNode.replaceChild(el_node,this.el);
            }
            this.el = el_node;

            var list_container = el_node.querySelector('.attribute-list');
            for(var i = 0, len = this.attribute_list.length; i < len; i++){
                var attribute_node = this.render_attribute(this.attribute_list[i]);
                attribute_node.querySelector('.attribute-name').addEventListener('click', this.click_reset_attribute_handler);
//                attribute_node.addEventListener('click', this.click_reset_attribute_handler);
                list_container.appendChild(attribute_node);
            };
        },

    });

    module.UsernameWidget = module.PosBaseWidget.extend({
        template: 'UsernameWidget',
        init: function(parent, options){
            var self = this;
            var options = options || {};
            this._super(parent,options);
            this.mode = options.mode || 'cashier';

            this.$el.click(function(){
                self.show_select_users_screen();
            });
        },
        set_user_mode: function(mode){
            this.mode = mode;
            this.refresh();
        },
        refresh: function(){
            this.renderElement();
        },
        get_name: function(){
            var user;
            if(this.mode === 'cashier'){
                user = this.pos.cashier || this.pos.user;
            }else{
                user = this.pos.get('selectedOrder').get_client()  || this.pos.user;
            }
            if(user){
                return user.name;
            }else{
                return "";
            }
        },
        get_image: function(){
            var user;
            user = this.pos.cashier || false;
            if(user){
                return user.image;
            }else{
                return "";
            }
        },
        show_select_users_screen: function() {
            /**
             * Check current screen is receipt or not?
             * for make sure selectedOrder was destroyed -> cart clear
             */
            var current_screen = this.pos_widget.screen_selector.get_current_screen();
            if (current_screen !== 'receipt') {
                    this.pos_widget.screen_selector.set_current_screen('selectuser');
            }
        },
    });

    module.HeaderButtonWidget = module.PosBaseWidget.extend({
        template: 'HeaderButtonWidget',
        init: function(parent, options){
            options = options || {};
            this._super(parent, options);
            this.action = options.action;
            this.label   = options.label;
        },
        renderElement: function(){
            var self = this;
            this._super();
            if(this.action){
                this.$el.click(function(){
                    self.action();
                });
            }
        },
        show: function(){ this.$el.removeClass('oe_hidden'); },
        hide: function(){ this.$el.addClass('oe_hidden'); },
    });

    // The debug widget lets the user control and monitor the hardware and software status
    // without the use of the proxy
    module.DebugWidget = module.PosBaseWidget.extend({
        template: "DebugWidget",
        eans:{
            admin_badge:  '0410100000006',
            client_badge: '0420200000004',
            invalid_ean:  '1232456',
            soda_33cl:    '5449000000996',
            oranges_kg:   '2100002031410',
            lemon_price:  '2301000001560',
            unknown_product: '9900000000004',
        },
        events:[
            'open_cashbox',
            'print_receipt',
            'scale_read',
        ],
        minimized: false,
        init: function(parent,options){
            this._super(parent,options);
            var self = this;

            this.minimized = false;

            // for dragging the debug widget around
            this.dragging  = false;
            this.dragpos = {x:0, y:0};

            function eventpos(event){
                if(event.touches && event.touches[0]){
                    return {x: event.touches[0].screenX, y: event.touches[0].screenY};
                }else{
                    return {x: event.screenX, y: event.screenY};
                }
            }

            this.dragend_handler = function(event){
                self.dragging = false;
            };
            this.dragstart_handler = function(event){
                self.dragging = true;
                self.dragpos = eventpos(event);
            };
            this.dragmove_handler = function(event){
                if(self.dragging){
                    var top = this.offsetTop;
                    var left = this.offsetLeft;
                    var pos  = eventpos(event);
                    var dx   = pos.x - self.dragpos.x; 
                    var dy   = pos.y - self.dragpos.y; 

                    self.dragpos = pos;

                    this.style.right = 'auto';
                    this.style.bottom = 'auto';
                    this.style.left = left + dx + 'px';
                    this.style.top  = top  + dy + 'px';
                }
                event.preventDefault();
                event.stopPropagation();
            };
        },
        start: function(){
            var self = this;

            this.el.addEventListener('mouseleave', this.dragend_handler);
            this.el.addEventListener('mouseup',    this.dragend_handler);
            this.el.addEventListener('touchend',   this.dragend_handler);
            this.el.addEventListener('touchcancel',this.dragend_handler);
            this.el.addEventListener('mousedown',  this.dragstart_handler);
            this.el.addEventListener('touchstart', this.dragstart_handler);
            this.el.addEventListener('mousemove',  this.dragmove_handler);
            this.el.addEventListener('touchmove',  this.dragmove_handler);

            this.$('.toggle').click(function(){
                var content = self.$('.content');
                var bg      = self.$el;
                if(!self.minimized){
                    content.animate({'height':'0'},200);
                }else{
                    content.css({'height':'auto'});
                }
                self.minimized = !self.minimized;
            });
            this.$('.button.set_weight').click(function(){
                var kg = Number(self.$('input.weight').val());
                if(!isNaN(kg)){
                    self.pos.proxy.debug_set_weight(kg);
                }
            });
            this.$('.button.reset_weight').click(function(){
                self.$('input.weight').val('');
                self.pos.proxy.debug_reset_weight();
            });
            this.$('.button.custom_ean').click(function(){
                var ean = self.pos.barcode_reader.sanitize_ean(self.$('input.ean').val() || '0');
                self.$('input.ean').val(ean);
                self.pos.barcode_reader.scan(ean);
            });
            this.$('.button.reference').click(function(){
                self.pos.barcode_reader.scan(self.$('input.ean').val());
            });
            this.$('.button.show_orders').click(function(){
                self.pos.pos_widget.screen_selector.show_popup('unsent-orders');
            });
            this.$('.button.delete_orders').click(function(){
                self.pos.pos_widget.screen_selector.show_popup('confirm',{
                    message: _t('Delete Unsent Orders ?'),
                    comment: _t('This operation will permanently destroy all unsent orders from the local storage. You will lose all the data. This operation cannot be undone.'),
                    confirm: function(){
                        self.pos.db.remove_all_orders();
                        self.pos.set({synch: { state:'connected', pending: 0 }});
                    },
                });
            });
            _.each(this.eans, function(ean, name){
                self.$('.button.'+name).click(function(){
                    self.$('input.ean').val(ean);
                    self.pos.barcode_reader.scan(ean);
                });
            });
            _.each(this.events, function(name){
                self.pos.proxy.add_notification(name,function(){
                    self.$('.event.'+name).stop().clearQueue().css({'background-color':'#6CD11D'}); 
                    self.$('.event.'+name).animate({'background-color':'#1E1E1E'},2000);
                });
            });
        },
    });

// ---------- Main Point of Sale Widget ----------

    module.StatusWidget = module.PosBaseWidget.extend({
        status: ['connected','connecting','disconnected','warning'],
        set_status: function(status,msg){
            var self = this;
            for(var i = 0; i < this.status.length; i++){
                this.$('.js_'+this.status[i]).addClass('oe_hidden');
            }
            this.$('.js_'+status).removeClass('oe_hidden');

            if(msg){
                this.$('.js_msg').removeClass('oe_hidden').html(msg);
            }else{
                this.$('.js_msg').addClass('oe_hidden').html('');
            }
        },
    });


    module.TrashStatusWidget = module.PosBaseWidget.extend({
        set_status: function(status,msg){
            var self = this;
            this.$('.js_trash_full').addClass('oe_hidden');
            this.$('.js_trash_empty').addClass('oe_hidden');
            this.$('.js_trash_'+status).removeClass('oe_hidden');

            if(msg){
                this.$('.js_msg').removeClass('oe_hidden').html(msg);
            }else{
                this.$('.js_msg').addClass('oe_hidden').html('');
            }
        },
    })

    // this manage trash
    module.TrashWidget = module.TrashStatusWidget.extend({
        template: 'TrashWidget',
        start: function(){
                var self = this;
                this.pos.bind('change:trash', function(pos,trashed){
                self.set_status(trashed.state, trashed.pending);
            });
            this.$el.click(function(){
                //self.pos.push_order();
            });
        },
    });
    // this is used to notify the user that data is being synchronized on the network
    module.SynchNotificationWidget = module.StatusWidget.extend({
        template: 'SynchNotificationWidget',
        start: function(){
            var self = this;
            this.pos.bind('change:synch', function(pos,synch){
                self.set_status(synch.state, synch.pending);
            });
            this.$el.click(function(){
                self.pos.push_order();
            });
        },
    });

    // this is used to notify the user if the pos is connected to the proxy
    module.ProxyStatusWidget = module.StatusWidget.extend({
        template: 'ProxyStatusWidget',
        set_smart_status: function(status){
            if(status.status === 'connected'){
                var warning = false;
                var msg = ''
                if(this.pos.config.iface_scan_via_proxy){
                    var scanner = status.drivers.scanner ? status.drivers.scanner.status : false;
                    if( scanner != 'connected' && scanner != 'connecting'){
                        warning = true;
                        msg += _t('Scanner');
                    }
                }
                if( this.pos.config.iface_print_via_proxy || 
                    this.pos.config.iface_fprint_via_proxy || 
                    this.pos.config.iface_cashdrawer ){
                    var printer = status.drivers.escpos ? status.drivers.escpos.status : false;
                    if( printer != 'connected' && printer != 'connecting'){
                        warning = true;
                        msg = msg ? msg + ' & ' : msg;
                        msg += _t('Printer');
                    }
                    var fprinter = status.drivers.fprinter ? status.drivers.fprinter.status : false;
                    if( fprinter != 'connected' && fprinter != 'connecting'){
                        warning = true;
                        msg = msg ? msg + ' & ' : msg;
                        msg += _t('Fiscal printer');
                    }
                }
                if( this.pos.config.iface_electronic_scale ){
                    var scale = status.drivers.scale ? status.drivers.scale.status : false;
                    if( scale != 'connected' && scale != 'connecting' ){
                        warning = true;
                        msg = msg ? msg + ' & ' : msg;
                        msg += _t('Scale');
                    }
                }
                msg = msg ? msg + ' ' + _t('Offline') : msg;
                this.set_status(warning ? 'warning' : 'connected', msg);
            }else{
                this.set_status(status.status,'');
            }
        },
        start: function(){
            var self = this;

            this.set_smart_status(this.pos.proxy.get('status'));

            this.pos.proxy.on('change:status',this,function(eh,status){ //FIXME remove duplicate changes 
                self.set_smart_status(status.newValue);
            });

            this.$el.click(function(){
                self.pos.connect_to_proxy();
            });
        },
    });


    // The PosWidget is the main widget that contains all other widgets in the PointOfSale.
    // It is mainly composed of :
    // - a header, containing the list of orders
    // - a leftpane, containing the list of bought products (orderlines) 
    // - a rightpane, containing the screens (see pos_screens.js)
    // - an actionbar on the bottom, containing various action buttons
    // - popups
    // - an onscreen keyboard
    // a screen_selector which controls the switching between screens and the showing/closing of popups

    module.PosWidget = module.PosBaseWidget.extend({
        template: 'PosWidget',
        init: function() { 
            this._super(arguments[0],{});

            this.pos = new module.PosModel(this.session,{pos_widget:this});
            this.pos_widget = this; //So that pos_widget's childs have pos_widget set automatically

            this.numpad_visible = true;
            this.leftpane_visible = true;
            this.topheader_visible = true;
            this.users_topheader_visible = false;
            this.leftpane_width   = '444px';
            this.cashier_controls_visible = true;
            this.screen_messages;

            FastClick.attach(document.body);

        },

        disable_rubberbanding: function(){
            // prevent the pos body from being scrollable. 
            document.body.addEventListener('touchmove',function(event){
                var node = event.target;
                while(node){
                    if(node.classList && node.classList.contains('touch-scrollable')){
                        return;
                    }
                    node = node.parentNode;
                }
                event.preventDefault();
            });
        },

        start: function() {
            var self = this;
            return self.pos.ready.done(function() {
                if ($.browser.chrome) {
                    var chrome_version = $.browser.version.split('.')[0];
                    if (parseInt(chrome_version, 10) >= 50) {
                        openerp.loadCSS('/point_of_sale/static/src/css/chrome50.css');
                    }
                }

                // remove default webclient handlers that induce click delay
                $(document).off();
                $(window).off();
                $('html').off();
                $('body').off();
                $(self.$el).parent().off();
                $('document').off();
                $('.oe_web_client').off();
                $('.openerp_webclient_container').off();

                self.renderElement();

                self.$('.neworder-button').click(function(){
                    self.pos.add_new_order();
                });

                self.$('.deleteorder-button').click(function(){
                    if( !self.pos.get('selectedOrder').is_empty() ){
                        self.screen_selector.show_popup('confirm',{
                            message: _t('Destroy Current Order ?'),
                            comment: _t('You will lose any data associated with the current order'),
                            confirm: function(){
                                self.pos.delete_current_order();
                            },
                        });
                    }else{
                        self.pos.delete_current_order();
                    }
                });

                self.$('.load-button').click(function(){
                    var ss = self.screen_selector;
                    ss.set_current_screen('orderlist');
                });
                self.$('.load-button').removeClass('oe_hidden');

                self.$('.save-button').click(function(){
                    self.screen_selector.show_popup('confirm',{
                        message: _t('Save The current Order ?'),
                        comment: _t('This operation will save the current order in a draft state. You\'ll have to mark it as paid after.'),
                        confirm: function(){
                            var currentOrder = self.pos.get('selectedOrder');
                            currentOrder.set_order_state('draft');
                            self.pos.push_order(currentOrder);
                            self.pos.get('selectedOrder').destroy();
                        },
                    });
                });
                self.$('.save-button').addClass('oe_hidden');

                //when a new order is created, add an order button widget
                self.pos.get('orders').bind('add', function(new_order){
                    var new_order_button = new module.OrderButtonWidget(null, {
                        order: new_order,
                        pos: self.pos
                    });
                    new_order_button.appendTo(this.$('.orders'));
                    new_order_button.selectOrder();
                }, self);

                self.pos.add_new_order();

                self.build_widgets();

                //if(self.pos.config.iface_big_scrollbars){
                //    self.$el.addClass('big-scrollbars');
                //}

                self.screen_selector.set_default_screen();

                self.pos.barcode_reader.connect();

                instance.webclient.set_content_full_screen(true);

                self.$('.loader').animate({opacity:0},1500,'swing',function(){self.$('.loader').addClass('oe_hidden');});

                instance.web.cordova.send('posready');

                self.pos.push_order();

            }).fail(function(err){   // error when loading models data from the backend
                self.loading_error(err);
            });
        },
        loading_error: function(err){
            var self = this;

            var message = err.message;
            var comment = err.stack;

            if(err.message === 'XmlHttpRequestError '){
                message = 'Network Failure (XmlHttpRequestError)';
                comment = 'The Point of Sale could not be loaded due to a network problem.\n Please check your internet connection.';
            }else if(err.message === 'OpenERP Server Error'){
                message = err.data.message;
                comment = err.data.debug;
            }

            if( typeof comment !== 'string' ){
                comment = 'Traceback not available.';
            }

            var popup = $(QWeb.render('ErrorTracebackPopupWidget',{
                widget: { message: message, comment: comment },
            }));

            popup.find('.button').click(function(){
                self.close();
            });

            popup.css({ zindex: 9001 });

            popup.appendTo(this.$el);
        },
        loading_progress: function(fac){
            this.$('.loader .loader-feedback').removeClass('oe_hidden');
            this.$('.loader .progress').css({'width': ''+Math.floor(fac*100)+'%'});
        },
        loading_message: function(msg,progress){
            this.$('.loader .loader-feedback').removeClass('oe_hidden');
            this.$('.loader .message').text(msg);
            if(typeof progress !== 'undefined'){
                this.loading_progress(progress);
            }
        },
        loading_skip: function(callback){
            if(callback){
                this.$('.loader .loader-feedback').removeClass('oe_hidden');
                this.$('.loader .button.skip').removeClass('oe_hidden');
                this.$('.loader .button.skip').off('click');
                this.$('.loader .button.skip').click(callback);
            }else{
                this.$('.loader .button.skip').addClass('oe_hidden');
            }
        },
        // This method instantiates all the screens, widgets, etc. If you want to add new screens change the
        // startup screen, etc, override this method.
        build_widgets: function() {
            var self = this;

            // --------  Error messages --
            this.screen_messages = new module.ErrorsWidget(this, {});

            // --------  Screens ---------
            this.product_screen = new module.ProductScreenWidget(this,{});
            this.product_screen.appendTo(this.$('.screens'));

            this.product_filtered_screen = new module.ProductScreenWidget(this,{noHeader: true, emptyList: true, infoHeader: true});
            this.product_filtered_screen.appendTo(this.$('.screens'));

            this.receipt_screen = new module.ReceiptScreenWidget(this, {});
            this.receipt_screen.appendTo(this.$('.screens'));

            this.payment_screen = new module.PaymentScreenWidget(this, {});
            this.payment_screen.appendTo(this.$('.screens'));

            this.clientlist_screen = new module.ClientListScreenWidget(this, {});
            this.clientlist_screen.appendTo(this.$('.screens'));

            this.scale_screen = new module.ScaleScreenWidget(this,{});
            this.scale_screen.appendTo(this.$('.screens'));

            this.selectusers = new module.UsersSelectionScreenWidget(this, this.pos.db.users);
            this.selectusers.appendTo(this.$('.screens'));
            console.log("UsersSelectionScreenWidget", this.selectusers)
            // New Screen to select Draft Orders
            this.orderlist_screen = new module.OrderListScreenWidget(this, {});
            this.orderlist_screen.appendTo(this.$('.screens'));
            this.orderlist_screen.hide();

            // --------  Popups ---------

            this.error_popup = new module.ErrorPopupWidget(this, {});
            this.error_popup.appendTo(this.$el);

            this.error_barcode_popup = new module.ErrorBarcodePopupWidget(this, {});
            this.error_barcode_popup.appendTo(this.$el);

            this.error_traceback_popup = new module.ErrorTracebackPopupWidget(this,{});
            this.error_traceback_popup.appendTo(this.$el);

            this.confirm_popup = new module.ConfirmPopupWidget(this,{});
            this.confirm_popup.appendTo(this.$el);

            this.unsent_orders_popup = new module.UnsentOrdersPopupWidget(this,{});
            this.unsent_orders_popup.appendTo(this.$el);

            this.password_confirm_popup = new module.PasswordConfirmPopupWidget(this,{});
            this.password_confirm_popup.appendTo(this.$el);

            this.select_variant_popup = new module.SelectVariantPopupWidget(this, {});
            this.select_variant_popup.appendTo($(this.$el));

            // --------  Misc ---------
            this.trashorders = new module.TrashWidget(this,{});
            this.trashorders.appendTo(this.$('.pos-rightheader'));

            this.notification = new module.SynchNotificationWidget(this,{});
            this.notification.appendTo(this.$('.pos-rightheader'));

            if(this.pos.config.use_proxy){
                this.proxy_status = new module.ProxyStatusWidget(this,{});
                this.proxy_status.appendTo(this.$('.pos-rightheader'));
            }

            this.close_button = new module.HeaderButtonWidget(this,{
                label: _t('Close'),
                action: function(){ 
                    var self = this;
                    if (!this.confirmed) {
                        this.$el.addClass('confirm');
                        this.$el.text(_t('Confirm'));
                        this.confirmed = setTimeout(function(){
                            self.$el.removeClass('confirm');
                            self.$el.text(_t('Close'));
                            self.confirmed = false;
                        },2000);
                    } else {
                        clearTimeout(this.confirmed);
                        this.pos_widget.close();
                    }
                },
            });
            this.close_button.appendTo(this.$('.pos-rightheader'));

            this.username   = new module.UsernameWidget(this,{});
            this.username.replace(this.$('.placeholder-UsernameWidget'));

            this.action_bar = new module.ActionBarWidget(this);
            this.action_bar.replace(this.$(".placeholder-RightActionBar"));

            this.paypad = new module.PaypadWidget(this, {});
            this.paypad.replace(this.$('.placeholder-PaypadWidget'));

            this.numpad = new module.NumpadWidget(this);
            this.numpad.replace(this.$('.placeholder-NumpadWidget'));

            this.order_widget = new module.OrderWidget(this, {});
            this.order_widget.replace(this.$('.placeholder-OrderWidget'));

            this.onscreen_keyboard = new module.OnscreenKeyboardWidget(this, {
                'keyboard_model': 'simple'
            });
            this.onscreen_keyboard.replace(this.$('.placeholder-OnscreenKeyboardWidget'));

            this.onscreen_controlbuttons = new module.OnscreenControlbuttonsWidget(this, {});
            this.onscreen_controlbuttons.replace(this.$('.placeholder-OnscreenControlbuttonsWidget'));

            // --------  Screen Selector ---------
            this.screen_selector = new module.ScreenSelector({
                pos: this.pos,
                screen_set:{
                    'selectusers': this.selectusers,
                    'products': this.product_screen,
                    'filtered_products': this.product_filtered_screen,
                    'payment' : this.payment_screen,
                    'scale':    this.scale_screen,
                    'receipt' : this.receipt_screen,
                    'clientlist': this.clientlist_screen,
                    'orderlist': this.orderlist_screen,
                    'select-variant-popup': this.select_variant_popup,
                    'control_buttons': this.onscreen_controlbuttons,
                },
                popup_set:{
                    'error': this.error_popup,
                    'error-barcode': this.error_barcode_popup,
                    'error-traceback': this.error_traceback_popup,
                    'confirm': this.confirm_popup,
                    'unsent-orders': this.unsent_orders_popup,
                    'password_confirm': this.password_confirm_popup,
                },
                default_screen: 'selectusers',// TODO 'products' replace with user selector
                default_mode: 'cashier',
            });

            if(this.pos.debug){
                this.debug_widget = new module.DebugWidget(this);
                this.debug_widget.appendTo(this.$('.pos-content'));
            }

            this.disable_rubberbanding();

        },

        changed_pending_operations: function () {
            var self = this;
            this.synch_notification.on_change_nbr_pending(self.pos.get('nbr_pending_operations').length);
        },
        // shows or hide the numpad and related controls like the paypad.
        set_numpad_visible: function(visible){
            if(visible !== this.numpad_visible){
                this.numpad_visible = visible;
                if(visible){
                    this.numpad.show();
                    this.paypad.show();
                }else{
                    this.numpad.hide();
                    this.paypad.hide();
                }
            }
        },
        //shows or hide the leftpane (contains the list of orderlines, the numpad, the paypad, etc.)
        set_leftpane_visible: function(visible){
            if(visible !== this.leftpane_visible){
                this.leftpane_visible = visible;
                if(visible){
                    this.$('.pos-leftpane').removeClass('oe_hidden');
                    this.$('.rightpane').css({'left':this.leftpane_width});
                }else{
                    this.$('.pos-leftpane').addClass('oe_hidden');
                    this.$('.rightpane').css({'left':'0px'});
                }
            }
        },
        set_topheader_visible: function(visible){
            if(visible !== this.topheader_visible){
                this.topheader_visible = visible;
                if(visible){
                    this.$('.pos-topheader').removeClass('oe_hidden');
                }else{
                    this.$('.pos-topheader').addClass('oe_hidden');
                }
            }
        },
        set_users_topheader_visible: function(visible){
            if(visible !== this.users_topheader_visible){
                this.users_topheader_visible = visible;
                if(visible){
                    this.$('.users-topheader').removeClass('oe_hidden');
                }else{
                    this.$('.users-topheader').addClass('oe_hidden');
                }
            }
        },
        close: function() {
            var self = this;

            function close(){
                self.pos.push_order().then(function(){
                    instance.web.cordova.send('poslogout');
                    return new instance.web.Model("ir.model.data").get_func("search_read")([['name', '=', 'action_client_pos_menu']], ['res_id']).pipe(function(res) {
                        window.location = '/web#action=' + res[0]['res_id'];
                    },function(err,event) {
                        event.preventDefault();
                        self.screen_selector.show_popup('error',{
                            'message': _t('Could not close the point of sale.'),
                            'comment': _t('Your internet connection is probably down.'),
                        });
                        self.close_button.renderElement();
                    });
                });
            }

            var draft_order = _.find( self.pos.get('orders').models, function(order){
                return order.get('orderLines').length !== 0 && order.get('paymentLines').length === 0;
            });
            if(draft_order){
                if (confirm(_t("Pending orders will be lost.\nAre you sure you want to leave this session?"))) {
                    close();
                }
            }else{
                close();
            }
        },
        destroy: function() {
            this.pos.destroy();
            instance.webclient.set_content_full_screen(false);
            this._super();
        }
    });
}
