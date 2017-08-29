function openerp_pos_models(instance, module){ //module is instance.point_of_sale
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;

    var round_di = instance.web.round_decimals;
    var round_pr = instance.web.round_precision

    // The PosModel contains the Point Of Sale's representation of the backend.
    // Since the PoS must work in standalone ( Without connection to the server ) 
    // it must contains a representation of the server's PoS backend. 
    // (taxes, product list, configuration options, etc.)  this representation
    // is fetched and stored by the PosModel at the initialisation. 
    // this is done asynchronously, a ready deferred alows the GUI to wait interactively 
    // for the loading to be completed 
    // There is a single instance of the PosModel for each Front-End instance, it is usually called
    // 'pos' and is available to all widgets extending PosWidget.

    module.PosModel = Backbone.Model.extend({
        initialize: function(session, attributes) {
            Backbone.Model.prototype.initialize.call(this, attributes);
            var  self = this;
            this.session = session;
            this.flush_mutex = new $.Mutex();                   // used to make sure the orders are sent to the server once at time
            this.pos_widget = attributes.pos_widget;

            this.proxy = new module.ProxyDevice(this);              // used to communicate to the hardware devices via a local proxy
            this.barcode_reader = new module.BarcodeReader({'pos': this, proxy:this.proxy, patterns: {}});  // used to read barcodes
            this.proxy_queue = new module.JobQueue();           // used to prevent parallels communications to the proxy
            this.db = new module.PosDB();                       // a local database used to search trough products and categories & store pending orders
            this.debug = jQuery.deparam(jQuery.param.querystring()).debug !== undefined;    //debug mode 

            // Price list engine
            this.pricelist_engine = new module.PricelistEngine({'pos': this, 'db': this.db, 'pos_widget': this.pos_widget});

            // Taxes engine
            this.taxes_engine = new module.TaxesEngine({'pos': this, 'db': this.db, 'pos_widget': this.pos_widget});

            // Business data; loaded from the server at launch
            this.accounting_precision = 2; //TODO
            this.company_logo = null;
            this.company_logo_base64 = '';
            this.currency = null;
            this.shop = null;
            this.company = null;
            this.user = null;
            this.users = [];
            this.partners = [];
            this.cashier = null;
            this.cashregisters = [];
            this.bankstatements = [];
            this.taxes = [];
            this.pos_session = null;
            this.config = null;
            this.units = [];
            this.units_by_id = {};
            this.pricelist = null;
            this.order_sequence = 1;
            window.posmodel = this;

            // these dynamic attributes can be watched for change by other models or widgets
            this.set({
                'synch':            { state:'connected', pending:0 }, 
                'orders':           new module.OrderCollection(),
                'selectedOrder':    null,
                'trashed':          { state:'empty', pending:0 },
                'trash':            new module.OrderCollection(),
            });

            this.bind('change:synch',function(pos,synch){
                clearTimeout(self.synch_timeout);
                self.synch_timeout = setTimeout(function(){
                    if(synch.state !== 'disconnected' && synch.pending > 0){
                        self.set('synch',{state:'disconnected', pending:synch.pending});
                    }
                },3000);
            });
            this.bind('change:trashed',function(pos,trashed){
                var pending = self.get('trash').length;
                if(pending > 0){
                    self.set('trashed', {state:'full', pending: pending});
                }
            });
            this.get('orders').bind('remove', function(order,_unused_,options){ 
                self.on_removed_order(order,options.index,options.reason); 
            });

            // We fetch the backend data on the server asynchronously. this is done only when the pos user interface is launched,
            // Any change on this data made on the server is thus not reflected on the point of sale until it is relaunched. 
            // when all the data has loaded, we compute some stuff, and declare the Pos ready to be used. 
            this.ready = this.load_server_data()
                .then(function(){
                    if(self.config.use_proxy){
                        return self.connect_to_proxy();
                    }
                });

        },

        // releases ressources holds by the model at the end of life of the posmodel
        destroy: function(){
            // FIXME, should wait for flushing, return a deferred to indicate successfull destruction
            // this.flush();
            this.proxy.close();
            this.barcode_reader.disconnect();
            this.barcode_reader.disconnect_from_proxy();
        },
        connect_to_proxy: function(){
            var self = this;
            var  done = new $.Deferred();
            this.barcode_reader.disconnect_from_proxy();
            this.pos_widget.loading_message(_t('Connecting to the PosBox'),0);
            this.pos_widget.loading_skip(function(){
                    self.proxy.stop_searching();
                });
            this.proxy.autoconnect({
                    force_ip: self.config.proxy_ip || undefined,
                    progress: function(prog){ 
                        self.pos_widget.loading_progress(prog);
                    },
                }).then(function(){
                    if(self.config.iface_scan_via_proxy){
                        self.barcode_reader.connect_to_proxy();
                    }
                }).always(function(){
                    done.resolve();
                });
            return done;
        },

        // helper function to load data from the server. Obsolete use the models loader below.
        fetch: function(model, fields, domain, ctx){
            this._load_progress = (this._load_progress || 0) + 0.05; 
            this.pos_widget.loading_message(_t('Loading')+' '+model,this._load_progress);
            return new instance.web.Model(model).query(fields).filter(domain).context(ctx).all()
        },

        // Server side model loaders. This is the list of the models that need to be loaded from
        // the server. The models are loaded one by one by this list's order. The 'loaded' callback
        // is used to store the data in the appropriate place once it has been loaded. This callback
        // can return a deferred that will pause the loading of the next module. 
        // a shared temporary dictionary is available for loaders to communicate private variables
        // used during loading such as object ids, etc. 
        models: [
        {
            model:  'res.users',
            fields: [ 'image_small', 'image_medium', 'name', 'ean13', 'cashier_password','company_id'],
            ids:    function(self){ return [self.session.uid]; },
            domain: function(self){
                return [['pos_config','=',self.session.uid]];
                },
            loaded: function(self,users){ 
                self.user = users[0];
                self.users = users;
                self.db.set_users(users);
                },
        },{
            model:  'res.company',
            fields: [ 'currency_id', 'email', 'website', 'company_registry', 'vat', 'name', 'phone', 'partner_id' , 'country_id', 'tax_calculation_rounding_method', 'lang'],
            ids:    function(self){ return [self.user.company_id[0]] },
            loaded: function(self,companies){ self.company = companies[0]; },
        },{
            model:  'decimal.precision',
            fields: ['name','digits'],
            loaded: function(self,dps){
                self.dp  = {};
                for (var i = 0; i < dps.length; i++) {
                    self.dp[dps[i].name] = dps[i].digits;
                }
            },
        },{ 
            model:  'product.uom',
            fields: [],
            domain: null,
            context: function(self){ return { active_test: false }; },
            loaded: function(self,units){
                self.units = units;
                var units_by_id = {};
                for(var i = 0, len = units.length; i < len; i++){
                    units_by_id[units[i].id] = units[i];
                    units[i].groupable = ( units[i].category_id[0] === 1 );
                    units[i].is_unit   = ( units[i].id === 1 );
                }
                self.units_by_id = units_by_id;
            }
        },{
            model:  'res.partner',
            fields: ['is_company','name','street','city','state_id','country_id','vat','phone','zip','mobile','email',
                     'ean13','write_date','lang','property_account_position', 'property_product_pricelist'],
            domain: [['customer','=',true]],
            loaded: function(self,partners){
                self.partners = partners;
                self.db.add_partners(partners);
            },
        },{
            model:  'res.country',
            fields: ['name'],
            loaded: function(self,countries){
                self.countries = countries;
                self.company.country = null;
                for (var i = 0; i < countries.length; i++) {
                    if (countries[i].id === self.company.country_id[0]){
                        self.company.country = countries[i];
                    }
                }
            },
        },{
            model:  'account.tax',
            fields: ['name','amount', 'price_include', 'include_base_amount', 'type', 'child_ids', 'child_depend', 'include_base_amount'],
            domain: null,
            loaded: function(self, taxes){
                self.taxes = taxes;
                self.taxes_by_id = {};
                _.each(taxes, function(tax){
                    self.taxes_by_id[tax.id] = tax;
                });
                _.each(self.taxes_by_id, function(tax) {
                    tax.child_taxes = {};
                    _.each(tax.child_ids, function(child_tax_id) {
                        tax.child_taxes[child_tax_id] = self.taxes_by_id[child_tax_id];
                    });
                });
            },
        },{
            model: 'account.fiscal.position.tax',
            fields: ['display_name', 'position_id', 'tax_src_id', 'tax_dest_id'],
            domain: null,
            loaded: function (self, fiscal_position_taxes) {
                self.db.add_fiscal_position_taxes(
                    fiscal_position_taxes
                );
                }
        },{
            model:  'pos.session',
            fields: ['id', 'journal_ids','name','user_id','config_id','start_at','stop_at','sequence_number','login_number'],
            domain: function(self){ return [['state','=','opened'],['user_id','=',self.session.uid]]; },
            loaded: function(self,pos_sessions){
                self.pos_session = pos_sessions[0]; 

                var orders = self.db.get_orders();
                for (var i = 0; i < orders.length; i++) {
                    self.pos_session.sequence_number = Math.max(self.pos_session.sequence_number, orders[i].data.sequence_number+1);
                }
            },
        },{
            model: 'pos.config',
            fields: [],
            domain: function(self){ return [['id','=',self.session.uid]]; },
            loaded: function(self,configs){
                self.config = configs[0];
                self.config.printers = [["escpos", self.config.iface_print_via_proxy],["fprinter", self.config.iface_fprint_via_proxy]]
                self.config.use_proxy = self.config.iface_payment_terminal ||
                                        self.config.iface_electronic_scale ||
                                        self.config.iface_print_via_proxy  ||
                                        self.config.iface_fprint_via_proxy ||
                                        self.config.iface_scan_via_proxy   ||
                                        self.config.iface_cashdrawer;
                self.db.set_required_password(self.config);
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
                console.log("Config pos_config", self.config);
            },
        },{
            model: 'stock.location',
            fields: [],
            ids:    function(self){ return [self.config.stock_location_id[0]]; },
            loaded: function(self, locations){ self.shop = locations[0]; },
        },{
            model:  'product.pricelist',
            fields: ['display_name', 'name', 'version_id', 'currency_id'],
            domain: function () {return [['type', '=', 'sale']]},
            //ids:    function(self){ return [self.config.pricelist_id[0]]; },
            //loaded: function(self, pricelists){ self.pricelist = pricelists[0]; },
            loaded: function (self, pricelists) {
                self.pricelist = pricelists[0];
                self.db.add_pricelists(pricelists);
                //console.log("add price list", pricelists, self.config.pricelist_id[0]);
            },
        },{
            model: 'product.pricelist.version',
            fields: ['name', 'pricelist_id', 'date_start', 'date_end', 'items'],
            domain: null,
            loaded: function (self, versions) {
                self.db.add_pricelist_versions(versions);
            },
        },{
            model: 'product.pricelist.item',
            fields: ['name', 'base', 'base_pricelist_id', 'categ_id', 'margin_classification_id', 'min_quantity', 'price_discount', 'price_max_margin', 'price_min_margin',
                     'price_round', 'price_surcharge', 'margin_classification_discount', 'price_version_id', 'product_id', 'product_tmpl_id', 'sequence'],
            domain: null,
            loaded: function (self, items) {
                self.db.add_pricelist_items(items);
            }
        },{
            model: 'product.price.type',
            fields: ['name', 'field', 'currency_id'],
            domain: null,
            loaded: function (self, price_types) {
                // we need to add price type
                // field to product.product model if not the case
                var product_model = _.find(this.models,function(model){ return model.model === 'product.product'; });
                for (var i = 0, len = price_types.length; i < len; i++) {
                    var p_type = price_types[i].field;
                    if (_.size(product_model) == 1) {
                        var product_index = parseInt(Object.keys(product_model)[0]);
                        if (posmodel.models[product_index].fields.indexOf(p_type) === -1) {
                            posmodel.models[product_index].fields.push(p_type);
                        }
                    }
                }
                self.db.add_price_types(price_types);
            },
        },{
            model: 'product.margin.classification',
            fields: ['name', 'margin'],
            domain: null,
            loaded: function (self, margins) {
                self.db.add_margin_classification(margins);
            }
        },{
            model: 'pricelist.partnerinfo',
            fields: ['display_name', 'min_quantity', 'name', 'price', 'suppinfo_id'],
            domain: null,
            loaded: function (self, pricelist_partnerinfos) {
                self.db.add_pricelist_partnerinfo(
                    pricelist_partnerinfos
                );
            },
        },{
            model: 'product.supplierinfo',
            fields: ['delay', 'name', 'min_qty', 'pricelist_ids', 'product_code', 'product_name', 'sequence', 'qty', 'product_tmpl_id'],
            domain: [['product_tmpl_id.available_in_pos','=',true]],
            loaded: function (self, supplierinfos) {
                self.db.add_supplierinfo(supplierinfos);
            },
        },{
            model: 'product.category',
            fields: ['name', 'display_name', 'parent_id', 'child_id'],
            domain: null,
            loaded: function (self, categories) {
                self.db.add_product_categories(categories);
            },
        },{
            model: 'res.currency',
            fields: ['name','symbol','position','rounding','accuracy'],
            ids:    function(self){ return [self.pricelist.currency_id[0]]; },
            loaded: function(self, currencies){
                self.currency = currencies[0];
                if (self.currency.rounding > 0) {
                    self.currency.decimals = Math.ceil(Math.log(1.0 / self.currency.rounding) / Math.log(10));
                } else {
                    self.currency.decimals = 0;
                }

            },
        },{
            model: 'product.packaging',
            fields: ['ean','product_tmpl_id'],
            domain: null,
            loaded: function(self, packagings){ 
                self.db.add_packagings(packagings);
            },
        },{
            model:  'pos.category',
            fields: ['id','name','parent_id','child_id','image'],
            domain: null,
            loaded: function(self, categories){
                self.db.add_categories(categories);
            },
        },{
            model:  'product.product',
            fields: ['display_name', 'name', 'list_price','price','lst_price','pos_categ_id','taxes_id', 'ean13', 'default_code',
                     'to_weight', 'uom_id', 'uos_id', 'uos_coeff', 'mes_type', 'description_sale', 'description', 'type',
                     'product_tmpl_id', 'income_pdt', 'expense_pdt', 'categ_id', 'seller_ids', 'attribute_value_ids', 'price_extra',],
            domain: [['sale_ok','=',true],['available_in_pos','=',true]],
            context: function(self){ return { pricelist: self.pricelist.id, display_default_code: false }; },
            loaded: function(self, products){
                self.db.add_products(products);
            },
        },{
            // Load Product Template
            model: 'product.template',
            fields: ['name', 'display_name', 'product_variant_ids', 'product_variant_count','margin_classification_id',],
            domain:  function(self){return [['sale_ok','=',true], ['available_in_pos','=',true],];},
            context: function(self){
                return {
                    pricelist: self.pricelist.id,
                    display_default_code: false,
                };},
            loaded: function(self, templates){
                 self.db.add_templates(templates);
            },
        },{
            // Load Product Attribute
            model: 'product.attribute',
            fields: ['name','value_ids',],
            loaded: function(self, attributes){
                 self.db.add_product_attributes(attributes);
            },
        },{
            // Load Product Attribute Value
            model: 'product.attribute.value',
            fields: ['name','attribute_id',],
            loaded: function(self, values){
                 self.db.add_product_attribute_values(values);
            },
        },{
            model:  'account.bank.statement',
            fields: ['account_id','currency','journal_id','state','name','user_id','pos_session_id'],
            domain: function(self){ return [['state', '=', 'open'],['pos_session_id', '=', self.pos_session.id]]; },
            loaded: function(self, bankstatements, tmp){
                self.bankstatements = bankstatements;

                tmp.journals = [];
                _.each(bankstatements,function(statement){
                    tmp.journals.push(statement.journal_id[0]);
                });
            },
        },{
            model:  'account.journal',
            fields: [],
            domain: function(self,tmp){ return [['id','in',tmp.journals]]; },
            loaded: function(self, journals){
                self.journals = journals;

                // associate the bank statements with their journals. 
                var bankstatements = self.bankstatements;
                for(var i = 0, ilen = bankstatements.length; i < ilen; i++){
                    for(var j = 0, jlen = journals.length; j < jlen; j++){
                        if(bankstatements[i].journal_id[0] === journals[j].id){
                            bankstatements[i].journal = journals[j];
                        }
                    }
                }
                self.cashregisters = bankstatements;
            },
        },{
            label: 'fonts',
            loaded: function(self){
                var fonts_loaded = new $.Deferred();

                // Waiting for fonts to be loaded to prevent receipt printing
                // from printing empty receipt while loading Inconsolata
                // ( The font used for the receipt ) 
                waitForWebfonts(['Lato','Inconsolata'], function(){
                    fonts_loaded.resolve();
                });

                // The JS used to detect font loading is not 100% robust, so
                // do not wait more than 5sec
                setTimeout(function(){
                    fonts_loaded.resolve();
                },5000);

                return fonts_loaded;
            },
        },{
            label: 'pictures',
            loaded: function(self){
                self.company_logo = new Image();
                var  logo_loaded = new $.Deferred();
                self.company_logo.onload = function(){
                    var img = self.company_logo;
                    var ratio = 1;
                    var targetwidth = 300;
                    var maxheight = 150;
                    if( img.width !== targetwidth ){
                        ratio = targetwidth / img.width;
                    }
                    if( img.height * ratio > maxheight ){
                        ratio = maxheight / img.height;
                    }
                    var width  = Math.floor(img.width * ratio);
                    var height = Math.floor(img.height * ratio);
                    var c = document.createElement('canvas');
                        c.width  = width;
                        c.height = height
                    var ctx = c.getContext('2d');
                        ctx.drawImage(self.company_logo,0,0, width, height);

                    self.company_logo_base64 = c.toDataURL();
                    logo_loaded.resolve();
                };
                self.company_logo.onerror = function(){
                    logo_loaded.reject();
                };
                    self.company_logo.crossOrigin = "anonymous";
                self.company_logo.src = '/web/binary/company_logo' +'?dbname=' + self.session.db + '&_'+Math.random();

                return logo_loaded;
            },
        },
        ],

        // loads all the needed data on the sever. returns a deferred indicating when all the data has loaded. 
        load_server_data: function(){
            var self = this;
            var loaded = new $.Deferred();
            var progress = 0;
            var progress_step = 1.0 / self.models.length;
            var tmp = {}; // this is used to share a temporary state between models loaders

            function load_model(index){
                if(index >= self.models.length){
                    loaded.resolve();
                }else{
                    var model = self.models[index];
                    self.pos_widget.loading_message(_t('Loading')+' '+(model.label || model.model || ''), progress);
                    var fields =  typeof model.fields === 'function'  ? model.fields(self,tmp)  : model.fields;
                    var domain =  typeof model.domain === 'function'  ? model.domain(self,tmp)  : model.domain;
                    var context = typeof model.context === 'function' ? model.context(self,tmp) : model.context; 
                    var ids     = typeof model.ids === 'function'     ? model.ids(self,tmp) : model.ids;
                    progress += progress_step;


                    if( model.model ){
                        if (model.ids) {
                            var records = new instance.web.Model(model.model).call('read',[ids,fields],context);
                        } else {
                            var records = new instance.web.Model(model.model).query(fields).filter(domain).context(context).all()
                        }
                        records.then(function(result){
                                try{    // catching exceptions in model.loaded(...)
                                    $.when(model.loaded(self,result,tmp))
                                        .then(function(){ load_model(index + 1); },
                                              function(err){ loaded.reject(err); });
                                }catch(err){
                                    loaded.reject(err);
                                }
                            },function(err){
                                loaded.reject(err);
                            });
                    }else if( model.loaded ){
                        try{    // catching exceptions in model.loaded(...)
                            $.when(model.loaded(self,tmp))
                                .then(  function(){ load_model(index +1); },
                                        function(err){ loaded.reject(err); });
                        }catch(err){
                            loaded.reject(err);
                        }
                    }else{
                        load_model(index + 1);
                    }
                }
            }

            try{
                load_model(0);
            }catch(err){
                loaded.reject(err);
            }

            return loaded;
        },

        // reload the list of partner, returns as a deferred that resolves if there were
        // updated partners, and fails if not
        load_new_partners: function(){
            var self = this;
            var def  = new $.Deferred();
            var fields = _.find(this.models,function(model){ return model.model === 'res.partner'; }).fields;
            new instance.web.Model('res.partner')
                .query(fields)
                .filter([['write_date','>',this.db.get_partner_write_date()]])
                .all({'timeout':3000, 'shadow': true})
                .then(function(partners){
                    if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                        def.resolve();
                    } else {
                        def.reject();
                    }
                }, function(err,event){ event.preventDefault(); def.reject(); });    
            return def;
        },

        // this is called when an order is removed from the order collection. It ensures that there is always an existing
        // order and a valid selected order
        on_removed_order: function(removed_order,index,reason){
            if( (reason === 'abandon' || removed_order.temporary) && this.get('orders').size() > 0){
                // when we intentionally remove an unfinished order, and there is another existing one
                this.set({'selectedOrder': this.get('orders').at(index) || this.get('orders').last()});
                this.pricelist_engine.update_products_ui(this.get('selectedOrder').get_client() || false);
            }else{
                // when the order was automatically removed after completion, 
                // or when we intentionally delete the only concurrent order
                this.add_new_order();
            }
        },

        //creates a new empty order and sets it as the current order
        add_new_order: function(){
            var ss = this.pos_widget.screen_selector;
            if (ss !== undefined && ss.get_current_screen() === 'filtered_products') {
                ss.set_current_screen('products');
            }
            var order = new module.Order({pos:this});
            this.get('orders').add(order);
            this.set('selectedOrder', order);
        },

        get_order: function(){
            return this.get('selectedOrder');
        },

        // restore orders from trash
        load_order_trash: function(order){
        },

        //removes the current order
        delete_current_order: function(){
            var selectedOrder = this.get('selectedOrder');
            this.get('trash').add(selectedOrder);
            this.set('trashed',{ state: 'full', pending: this.get('trash').length});

            selectedOrder.destroy({'reason':'abandon'});
        },

        // saves the order locally and try to send it to the backend. 
        // it returns a deferred that succeeds after having tried to send the order and all the other pending orders.
        push_order: function(order) {
            var self = this;

            if(order){
                console.log('Push order', order.export_as_JSON());
                this.proxy.log('push_order',order.export_as_JSON());
                this.db.add_order(order.export_as_JSON());
            }

            var pushed = new $.Deferred();

            this.flush_mutex.exec(function(){
                var flushed = self._flush_orders(self.db.get_orders());

                flushed.always(function(ids){
                    pushed.resolve();
                });
            });
            return pushed;
        },

        // saves the order locally and try to send it to the backend and make an invoice
        // returns a deferred that succeeds when the order has been posted and successfully generated
        // an invoice. This method can fail in various ways:
        // error-no-client: the order must have an associated partner_id. You can retry to make an invoice once
        //     this error is solved
        // error-transfer: there was a connection error during the transfer. You can retry to make the invoice once
        //     the network connection is up 

        push_and_invoice_order: function(order){
            var self = this;
            var invoiced = new $.Deferred(); 

            if(!order.get_client()){
                invoiced.reject('error-no-client');
                return invoiced;
            }

            var order_id = this.db.add_order(order.export_as_JSON());

            this.flush_mutex.exec(function(){
                var done = new $.Deferred(); // holds the mutex

                // send the order to the server
                // we have a 30 seconds timeout on this push.
                // FIXME: if the server takes more than 30 seconds to accept the order,
                // the client will believe it wasn't successfully sent, and very bad
                // things will happen as a duplicate will be sent next time
                // so we must make sure the server detects and ignores duplicated orders

                var transfer = self._flush_orders([self.db.get_order(order_id)], {timeout:30000, to_invoice:true});

                transfer.fail(function(){
                    invoiced.reject('error-transfer');
                    done.reject();
                });

                // on success, get the order id generated by the server
                transfer.pipe(function(order_server_id){

                    // generate the pdf and download it
                    self.pos_widget.do_action('point_of_sale.pos_invoice_report',{additional_context:{ 
                        active_ids:order_server_id,
                    }});

                    invoiced.resolve();
                    done.resolve();
                });

                return done;

            });

            return invoiced;
        },

        // wrapper around the _save_to_server that updates the synch status widget
        _flush_orders: function(orders, options) {
            var self = this;

            this.set('synch',{ state: 'connecting', pending: orders.length});

            return self._save_to_server(orders, options).done(function (server_ids) {
                var pending = self.db.get_orders().length;

                self.set('synch', {
                    state: pending ? 'connecting' : 'connected',
                    pending: pending
                });

                return server_ids;
            });
        },

        // send an array of orders to the server
        // available options:
        // - timeout: timeout for the rpc call in ms
        // returns a deferred that resolves with the list of
        // server generated ids for the sent orders
        _save_to_server: function (orders, options) {
            if (!orders || !orders.length) {
                var result = $.Deferred();
                result.resolve([]);
                return result;
            }

            options = options || {};

            var self = this;
            var timeout = typeof options.timeout === 'number' ? options.timeout : 7500 * orders.length;

            // we try to send the order. shadow prevents a spinner if it takes too long. (unless we are sending an invoice,
            // then we want to notify the user that we are waiting on something )
            var posOrderModel = new instance.web.Model('pos.order');
            return posOrderModel.call('create_from_ui',
                [_.map(orders, function (order) {
                    order.to_invoice = options.to_invoice || false;
                    return order;
                })],
                undefined,
                {
                    shadow: !options.to_invoice,
                    timeout: timeout
                }
            ).then(function (server_ids) {
                _.each(orders, function (order) {
                    self.db.remove_order(order.id);
                });
                return server_ids;
            }).fail(function (error, event){
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
                    self.pos_widget.screen_selector.show_popup('error-traceback',{
                        message: error.data.message,
                        comment: error.data.debug
                    });
                }
                // prevent an error popup creation by the rpc failure
                // we want the failure to be silent as we send the orders in the background
                event.preventDefault();
                console.error('Failed to send orders:', orders);
            });
        },

        scan_product: function(parsed_code){
            var self = this;
            var selectedOrder = this.get('selectedOrder');
            if(parsed_code.encoding === 'ean13'){
                var product = this.db.get_product_by_ean13(parsed_code.base_code);
            }else if(parsed_code.encoding === 'reference'){
                var product = this.db.get_product_by_reference(parsed_code.code);
            }

            if(!product){
                return false;
            }

            if(parsed_code.type === 'price'){
                selectedOrder.addProduct(product, {price:parsed_code.value});
            }else if(parsed_code.type === 'weight'){
                selectedOrder.addProduct(product, {quantity:parsed_code.value, merge:false});
            }else if(parsed_code.type === 'discount'){
                selectedOrder.addProduct(product, {discount:parsed_code.value, merge:false});
            }else{
                selectedOrder.addProduct(product, this.pricelist_engine.update_products_prices(product, selectedOrder.get_client()));
            }
            return true;
        },
    });

    var orderline_id = 1;

    // An orderline represent one element of the content of a client's shopping cart.
    // An orderline contains a product, its quantity, its price, discount. etc. 
    // An Order contains zero or more Orderlines.
    module.Orderline = Backbone.Model.extend({
        initialize: function(attr,options){
            this.pos = options.pos;
            this.order = options.order;
            this.product = options.product;
            this.price   = options.product.price;
            this.lst_price   = options.product.lst_price;
            this.set_quantity(1);
            this.discount = 0;
            this.discountStr = '0';
            this.type = 'unit';
            this.selected = false;
            this.id       = orderline_id++;
            this.order_id = -1;
            this.manual_price = false;
            this.force_merge = _.isEmpty(options.force_merge) ? false : options.force_merge;
            /*
            if (this.product !== undefined) {
                var qty = this.compute_qty(this.order, this.product);
                var price = this.pos.pricelist_engine.compute_price_all(this.pos.db, this.product, this.order.get_client() || null, qty);
                if (price !== false) {
                    this.set_unit_price({price: price, tax_included: true});
                }
            }
            */
        },
        clone: function(){
            var orderline = new module.Orderline({},{
                pos: this.pos,
                order: null,
                product: this.product,
                price: this.price,
                lst_price: this.lst_price,
            });
            orderline.quantity = this.quantity;
            orderline.quantityStr = this.quantityStr;
            orderline.discount = this.discount;
            orderline.type = this.type;
            orderline.selected = false;
            return orderline;
        },
        // sets a discount [0,100]%
        set_discount: function(discount){
            var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
            this.discount = disc;
            this.discountStr = '' + disc;
            this.trigger('change',this);
        },
        // returns the discount [0,100]%
        get_discount: function(){
            return this.discount;
        },
        get_discount_str: function(){
            return this.discountStr;
        },
        /**
         * @param state
         */
        set_manual_price: function (state) {
            this.manual_price = state;
        },
        get_product_type: function(){
            return this.type;
        },
        // sets the quantity of the product. The quantity will be rounded according to the 
        // product's unity of measure properties. Quantities greater than zero will not get 
        // rounded to zero
        set_quantity: function(quantity){
            if(quantity === 'remove'){
                this.order.removeOrderline(this);
                return;
            }else{
                var quant = parseFloat(quantity) || 0;
                var unit = this.get_unit();
                var partner = this.order ? this.order.get_client() : null;
                var product = this.product;
                var db = this.pos.db;
                var old_price = 0;
                var price = false;
                // first save old price
                if(this.quantity){
                    old_price = this.pos.pricelist_engine.compute_price_all(db, product, partner, this.quantity);
                }
                if(unit){
                    if (unit.rounding) {
                        this.quantity    = round_pr(quant, unit.rounding);
                        var decimals = Math.ceil(Math.log(1.0 / unit.rounding) / Math.log(10));
                        this.quantityStr = openerp.instances[this.pos.session.name].web.format_value(this.quantity, { type: 'float', digits: [69, decimals]});
                    } else {
                        this.quantity    = round_pr(quant, 1);
                        this.quantityStr = this.quantity.toFixed(0);
                    }
                }else{
                    this.quantity    = quant;
                    this.quantityStr = '' + this.quantity;
                }
                // parce price with new quantity
                price = this.pos.pricelist_engine.compute_price_all(db, product, partner, this.quantity);
                if (price !== false && price !== old_price) {
                    this.set_unit_price(price);
                }
            }
            this.trigger('change',this);
        },
        // return the quantity of product
        get_quantity: function(){
            return this.quantity;
        },
        get_quantity_str: function(){
            return this.quantityStr;
        },
        get_quantity_str_with_unit: function(){
            var unit = this.get_unit();
            if(unit && !unit.is_unit){
                return this.quantityStr + ' ' + unit.name;
            }else{
                return this.quantityStr;
            }
        },
        // return the unit of measure of the product
        get_unit: function(){
            var unit_id = this.product.uom_id;
            if(!unit_id){
                return undefined;
            }
            unit_id = unit_id[0];
            if(!this.pos){
                return undefined;
            }
            return this.pos.units_by_id[unit_id];
        },
        // return the product of this orderline
        get_product: function(){
            return this.product;
        },
        // selects or deselects this orderline
        set_selected: function(selected){
            this.selected = selected;
            this.trigger('change',this);
        },
        // returns true if this orderline is selected
        is_selected: function(){
            return this.selected;
        },
        // when we add an new orderline we want to merge it with the last line to see reduce the number of items
        // in the orderline. This returns true if it makes sense to merge the two
        can_be_merged_with: function(orderline){
            if( this.get_product().id !== orderline.get_product().id){    //only orderline of the same product can be merged
                //console.log("id step");
                return false;
            }else if(!this.get_unit() || !this.get_unit().groupable){
                //console.log("Unit step");
                return false;
            }else if(this.get_product_type() !== orderline.get_product_type()){
                //console.log("type step", this.get_product_type(), orderline.get_product_type());
                return false;
            }else if(this.get_discount() > 0){             // we don't merge discounted orderlines
                //console.log("discount step");
                return false;
            }else if(this.price !== orderline.price){
                //console.log("price step", this.price, orderline.price);
                return false;
            }else if(!this.manual_price && this.get_product().id === orderline.get_product().id){
                return true;
            }else{
                return true;
            }
        },
        merge: function(orderline){
            var price = this.force_merge ? orderline.price : (this.get_quantity()*this.price + orderline.get_quantity()*orderline.price)/(this.get_quantity()+orderline.get_quantity());
            this.set_quantity(this.get_quantity() + orderline.get_quantity());
            this.set_unit_price({price: price, tax_included: false,});
        },
        export_as_JSON: function() {
            //console.log("Export order lines", this.get_product());
            return {
                qty: this.get_quantity(),
                price_unit: this.get_unit_price(),
                discount: this.get_discount(),
                product_id: this.get_product().id,
                product_type: this.get_product().type,
                order_id: this.get_order_id(),
                tax_ids: [[6, false, this.get_applicable_taxes_for_orderline()]],
            };
        },
        //used to create a json of the ticket, to be sent to the printer
        export_for_printing: function(){
            return {
                quantity:           this.get_quantity(),
                unit_name:          this.get_unit().name,
                price:              this.get_unit_price(),
                discount:           this.get_discount(),
                product_name:       this.get_product().display_name,
                price_display :     this.get_display_price(),
                price_with_tax :    this.get_price_with_tax(),
                price_without_tax:  this.get_price_without_tax(),
                tax:                this.get_tax(),
                product_description:      this.get_product().description,
                product_description_sale: this.get_product().description_sale,
                product_type:             this.get_product().type,
            };
        },
        get_order_id: function(){
            return this.order_id;
        },
        set_order_id: function(id){
            this.order_id = id;
        },
        get_id: function(){
            return this.id;
        },
        // changes the base price of the product for this orderline
        set_unit_price: function(price){
            var tax_included = true;
            if (typeof price === 'object') {
                var in_price = price.price;
                var tax_included = price.tax_included;
                price = in_price;
            }
            //console.log("set price", price, tax_included);
            var unit_price = this.get_all_prices({quantity: 1, unit_price: parseFloat(price), disc: 0, force_tax_included: tax_included,}).priceWithoutTax;
            //console.log("set price after", price, tax_included);
            this.price = round_di(unit_price || 0, this.pos.dp['Product Price']);
            this.trigger('change',this);
        },
        get_unit_price: function(){
            return round_di(this.price || 0, this.pos.dp['Product Price'])
        },
        get_unit_lst_price: function(){
            return round_di(this.lst_price || 0, this.pos.dp['Product Price'])
        },
        get_base_price:    function(){
            var rounding = this.pos.currency.rounding;
            return round_pr(this.get_unit_price() * this.get_quantity() * (1 - this.get_discount()/100), rounding);
        },
        get_display_price: function(){
            return this.get_base_price();
        },
        get_display_lst_price: function(){
            return this.get_price_with_tax();
        },
        get_price_without_tax: function(){
            return this.get_all_prices().priceWithoutTax;
        },
        get_price_with_tax: function(){
            return this.get_all_prices().priceWithTax;
        },
        get_tax: function(){
            return this.get_all_prices().tax;
        },
        get_applicable_taxes: function(){
            // Shenaningans because we need
            // to keep the taxes ordering.
            var ptaxes_ids = this.get_product().taxes_id;
            var ptaxes_set = {};
            var partner    = this.order ? this.order.get_client() : null;
            if (partner && partner.property_account_position) {
                ptaxes_ids = this.pos.db.map_tax(partner.property_account_position[0], ptaxes_ids);
            }
            for (var i = 0; i < ptaxes_ids.length; i++) {
                ptaxes_set[ptaxes_ids[i]] = true;
            }
            var taxes = [];
            for (var i = 0; i < this.pos.taxes.length; i++) {
                if (ptaxes_set[this.pos.taxes[i].id]) {
                    taxes.push(this.pos.taxes[i]);
                }
            }
            return taxes;
        },
        get_applicable_taxes_for_orderline: function(){
            var taxes = this.get_applicable_taxes();
            var tax_ids = [];
            for (var i = 0, len = taxes.length; i < len; i++){
                tax_ids.push(taxes[i].id);
            }
            return tax_ids;
        },
        get_tax_details: function(){
            return this.get_all_prices().taxDetails;
        },
        /**
         * @param order
         * @param product
         * @returns {number}
         */
        compute_qty: function (order, product) {
            var qty = 1;
            var orderlines = [];
            if (order && order.get('orderLines').models !== undefined) {
                orderlines = order.get('orderLines').models;
            }
            for (var i = 0; i < orderlines.length; i++) {
                if (orderlines[i].product.id === product.id && !orderlines[i].manual_price) {
                    qty += orderlines[i].quantity;
                }
            }
            return qty;
        },
        get_all_prices: function(options){
            if (arguments.length > 0){
                var qty = options.quantity || this.get_quantity();
                var unit_price = options.unit_price || this.get_unit_price();
                var discount = options.disc || this.get_discount();
                var tax_included = typeof options.force_tax_included === 'undefined' && false || options.force_tax_included;
                var product = options.product || this.get_product();
            } else {
                var qty = this.get_quantity();
                var unit_price = this.get_unit_price();
                var discount = this.get_discount();
                var tax_included = false;
                var product = this.get_product();
            }
            return this.pos.taxes_engine.get_all_prices({quantity: qty, unit_price: unit_price, disc: discount, force_tax_included: tax_included, product: product,});
        },
    });

    module.OrderlineCollection = Backbone.Collection.extend({
        model: module.Orderline,
    });

    // Every Paymentline contains a cashregister and an amount of money.
    module.Paymentline = Backbone.Model.extend({
        initialize: function(attributes, options) {
            this.amount = 0;
            this.cashregister = options.cashregister;
            this.name = this.cashregister.journal_id[1];
            this.selected = false;
            this.pos = options.pos;
            // ['money', 'advance', 'cash']
            this.set({type: 'money',});
        },
        //sets the amount of money on this payment line
        set_amount: function(value){
            this.amount = round_di(parseFloat(value) || 0, this.pos.currency.decimals);
            this.trigger('change:amount',this);
        },
        // returns the amount of money on this paymentline
        get_amount: function(){
            return this.amount;
        },
        get_amount_str: function(){
            return openerp.instances[this.pos.session.name].web.format_value(this.amount, {
                type: 'float', digits: [69, this.pos.currency.decimals]
            });
        },
        set_selected: function(selected){
            if(this.selected !== selected){
                this.selected = selected;
                this.trigger('change:selected',this);
            }
        },
        // returns the payment type: 'cash' | 'bank'
        get_type: function(){
            return this.cashregister.journal.type
        },
        set_money_type: function(value){
            this.set({type: value,});
        },
        get_money_type: function(){
            return this.get('type');
        },
        // returns the associated cashregister
        //exports as JSON for server communication
        export_as_JSON: function(){
            return {
                name: instance.web.datetime_to_str(new Date()),
                type: this.get_money_type(),
                statement_id: this.cashregister.id,
                account_id: this.cashregister.account_id[0],
                journal_id: this.cashregister.journal_id[0],
                amount: this.get_amount(),
                order_id: this.get_order_id(),
            };
        },
        //exports as JSON for receipt printing
        export_for_printing: function(){
            return {
                amount: this.get_amount(),
                journal: this.cashregister.journal_id[1],
            };
        },
    });

    module.PaymentlineCollection = Backbone.Collection.extend({
        model: module.Paymentline,
    });

    // An order more or less represents the content of a client's shopping cart (the OrderLines) 
    // plus the associated payment information (the Paymentlines) 
    // there is always an active ('selected') order in the Pos, a new one is created
    // automaticaly once an order is completed and sent to the server.
    module.Order = Backbone.Model.extend({
        initialize: function(attributes){
            Backbone.Model.prototype.initialize.apply(this, arguments);
            this.pos = attributes.pos; 
            this.sequence_number = this.pos.pos_session.sequence_number++;
            this.uid = this.generateUniqueId();
            this.set({
                creationDate:   new Date(),
                orderLines:     new module.OrderlineCollection(),
                paymentLines:   new module.PaymentlineCollection(),
                name:           _t("Order ") + this.uid,
                client:         null,
                state:          'new',
                product_filter: [],
                });
            this.selected_orderline   = undefined;
            this.selected_paymentline = undefined;
            this.screen_data = {};  // see ScreenSelector
            this.receipt_type = 'receipt';  // 'receipt' || 'invoice'
            this.temporary = attributes.temporary || false;
            return this;
        },
        is_empty: function(){
            return (this.get('orderLines').models.length === 0);
        },
        // Generates a public identification number for the order.
        // The generated number must be unique and sequential. They are made 12 digit long
        // to fit into EAN-13 barcodes, should it be needed 
        generateUniqueId: function() {
            function zero_pad(num,size){
                var s = ""+num;
                while (s.length < size) {
                    s = "0" + s;
                }
                return s;
            }
            return zero_pad(this.pos.pos_session.id,5) +'-'+
                   zero_pad(this.pos.pos_session.login_number,3) +'-'+
                   zero_pad(this.sequence_number,4);
        },
        addOrderline: function(line){
            if(line.order){
                line.order.removeOrderline(line);
            }
            line.order = this;
            this.get('orderLines').add(line);
            this.selectLine(this.getLastOrderline());
        },
        findProduct(line){
            var orderLines = this.get('orderLines').models;
            var orderLine = undefined;
            //console.log("order lines", orderLines.length, orderLines, line);
            for (var i=0, len=orderLines.length; i<len; i++){
                //console.log("order lines product id", orderLines[i].can_be_merged_with(line), line.get_product().id, orderLines[i].get_product().id);
                if(orderLines[i].can_be_merged_with(line)){
                    orderLine = orderLines[i];
                    break;
                }
            }
            return orderLine;
        },
        addProduct: function(product, options){
            if(this._printed){
                this.destroy();
                return this.pos.get('selectedOrder').addProduct(product, options);
            }

            options = options || {};
            var attr = JSON.parse(JSON.stringify(product));
            attr.pos = this.pos;
            attr.order = this;
            var line = new module.Orderline({}, {pos: this.pos, order: this, product: product});
            if(options.order_id !== undefined){
                line.set_order_id(options.order_id);
            }
            if(options.quantity !== undefined){
                line.set_quantity(options.quantity);
            }
            if(options.price !== undefined){
                line.set_unit_price(options.price);
            }
            if(options.discount !== undefined){
                line.set_discount(options.discount);
            }
            var last_orderline = this.findProduct(line);
            if( last_orderline && options.merge !== false){
                var curr_qty = Math.abs(last_orderline.get_quantity()+line.get_quantity());
                var max_qty = Math.abs(product.max_qty || curr_qty);
                console.log("AddProduct", last_orderline, product.max_qty, max_qty, curr_qty, options.merge);
                if(curr_qty <= max_qty){
                    last_orderline.merge(line);
                }
            }else{
                this.get('orderLines').add(line);
                last_orderline = this.getLastOrderline();
            }
            this.selectLine(last_orderline);
        },
        removeOrderline: function( line ){
            this.get('orderLines').remove(line);
            this.selectLine(this.getLastOrderline());
        },
        getOrderline: function(id){
            var orderlines = this.get('orderLines').models;
            for(var i = 0; i < orderlines.length; i++){
                if(orderlines[i].id === id){
                    return orderlines[i];
                }
            }
            return null;
        },
        getOrderline_by_order_id: function(id){
            var orderlines = this.get('orderLines').models;
            var retOrderlines = [];
            //console.log("Get order line first", orderlines, orderlines.length);
            for(var i = 0; i < orderlines.length; i++){
                var order_id = orderlines[i].get_order_id() || 0;
                //console.log("Get order line", order_id, id);
                if( order_id === id){
                    retOrderlines.push(orderlines[i]);
                }
            }
            return retOrderlines;
        },
        getLastOrderline: function(){
            return this.get('orderLines').at(this.get('orderLines').length -1);
        },
        addPaymentline: function(cashregister) {
            console.log('Add payment', this.get('paymentLines'));
            var paymentAdvance = this.getPaidAdvance();
            var moneyinout = this.getMoneyInOut();
            var paymentLines = this.get('paymentLines');
            var newPaymentline = new module.Paymentline({},{cashregister:cashregister, pos:this.pos});
            var inx = _.find(paymentLines.models, function(x) { return ['advance','cash'].indexOf(x.type) !== -1;});
            // search for advance or moneyin/out line
            if(paymentAdvance !== 0){
                newPaymentline.set_amount( Math.max(paymentAdvance,0) );
            }
            if(cashregister.journal.type !== 'cash'){
                newPaymentline.set_amount( Math.max(this.getDueLeft(),0) );
            }
            newPaymentline.set_money_type(paymentAdvance !== 0 && 'advance' || newPaymentline.get_money_type());
            newPaymentline.set_money_type(moneyinout !== 0 && 'cash' || newPaymentline.get_money_type());
            console.log("add Payments", inx, _, paymentLines);
            //if(inx){
            //    paymentLines[inx] = newPaymentline;
            //} else {
                paymentLines.add(newPaymentline);
            //}
            this.selectPaymentline(newPaymentline);
            console.log("Add payment line", paymentAdvance);
        },
        removePaymentline: function(line){
            if(this.selected_paymentline === line){
                this.selectPaymentline(undefined);
            }
            this.get('paymentLines').remove(line);
        },
        get_order_state: function() {
            return this.get('state');
        },
        set_order_state: function(state) {
            this.set({state: state});
        },
        get_product_filter: function() {
            return this.get('product_filter');
        },
        set_product_filter: function(products) {
            this.set({product_filter: products});
        },
        set_order_id: function(id) {
            this.set({order_id: id,});
        },
        get_order_id: function() {
            return this.get('order_id');
        },
        set_order_ids: function(ids) {
            this.set({order_ids: ids,});
        },
        get_order_ids: function() {
            return this.get('order_ids');
        },
        setName: function(name) {
            this.set({name: name});
        },
        getName: function() {
            return this.get('name');
        },
        getSubtotal: function(){
            return round_pr((this.get('orderLines')).reduce((function(sum, orderLine){
                return sum + orderLine.get_display_price();
            }), 0), this.pos.currency.rounding);
        },
        getTotalTaxIncluded: function(types) {
            return this.getTotalTaxExcluded(types) + this.getTax(types);
        },
        getDiscountTotal: function() {
            return round_pr((this.get('orderLines')).reduce((function(sum, orderLine) {
                return sum + (orderLine.get_unit_price() * (orderLine.get_discount()/100) * orderLine.get_quantity());
            }), 0), this.pos.currency.rounding);
        },
        getTotalTaxExcluded: function(types) {
            var product_type = types || ['product','consu','service'];
            return round_pr((this.get('orderLines')).reduce((function(sum, orderLine) {
                //console.log("Calculate", product_type.indexOf(orderLine.get_product().type));
                return product_type.indexOf(orderLine.get_product().type) !== -1  && sum + orderLine.get_price_without_tax() || sum;
            }), 0), this.pos.currency.rounding);
        },
        getTax: function(types) {
            var product_type = types || ['product','consu','service'];
            return round_pr((this.get('orderLines')).reduce((function(sum, orderLine) {
                return product_type.indexOf(orderLine.get_product().type) !== -1 && sum + orderLine.get_tax() || sum;
            }), 0), this.pos.currency.rounding);
        },
        getTaxDetails: function(){
            var details = {};
            var fulldetails = [];

            this.get('orderLines').each(function(line){
                var ldetails = line.get_tax_details();
                for(var id in ldetails){
                    if(ldetails.hasOwnProperty(id)){
                        details[id] = (details[id] || 0) + ldetails[id];
                    }
                }
            });

            for(var id in details){
                if(details.hasOwnProperty(id)){
                    fulldetails.push({amount: details[id], tax: this.pos.taxes_by_id[id], name: this.pos.taxes_by_id[id].name});
                }
            }

            return fulldetails;
        },
        getPaidTotal: function(money) {
            var payment_money = money || ['money', 'advance', 'cash']; // calculate all by default
            return round_pr((this.get('paymentLines')).reduce((function(sum, paymentLine) {
                return  payment_money.indexOf(paymentLine.get_money_type()) !== -1 && sum + paymentLine.get_amount() || sum;
            }), 0), this.pos.currency.rounding);
        },
        getChange: function() {
            return this.getPaidTotal(['money']) - this.getTotalTaxIncluded();
        },
        getDueLeft: function() {
            return this.getTotalTaxIncluded() - this.getPaidTotal(['money']) - Math.abs(this.getPaidAdvance());
        },
        getPaidAdvance: function() {
            return this.getTotalTaxIncluded(['money']);
        },
        getMoneyInOut: function() {
            return this.getTotalTaxIncluded(['moneyin','moneyout']);
        },
        // sets the type of receipt 'receipt'(default) or 'invoice'
        set_receipt_type: function(type){
            this.receipt_type = type;
        },
        get_receipt_type: function(){
            return this.receipt_type;
        },
        // the client related to the current order.
        set_client: function(client){
            this.set('client',client);
        },
        get_client: function(){
            return this.get('client');
        },
        get_client_name: function(){
            var client = this.get('client');
            return client ? client.name : "";
        },
        // the order also stores the screen status, as the PoS supports
        // different active screens per order. This method is used to
        // store the screen status.
        set_screen_data: function(key,value){
            if(arguments.length === 2){
                this.screen_data[key] = value;
            }else if(arguments.length === 1){
                for(key in arguments[0]){
                    this.screen_data[key] = arguments[0][key];
                }
            }
        },
        //see set_screen_data
        get_screen_data: function(key){
            return this.screen_data[key];
        },
        // exports a JSON for receipt printing
        export_for_printing: function(){
            var orderlines = [];
            this.get('orderLines').each(function(orderline){
                orderlines.push(orderline.export_for_printing());
            });

            var paymentlines = [];
            this.get('paymentLines').each(function(paymentline){
                paymentlines.push(paymentline.export_for_printing());
            });
            var client  = this.get('client');
            var cashier = this.pos.cashier || this.pos.user;
            var company = this.pos.company;
            var shop    = this.pos.shop;
            var date = new Date();

            return {
                orderlines: orderlines,
                paymentlines: paymentlines,
                subtotal: this.getSubtotal(),
                total_with_tax: this.getTotalTaxIncluded(),
                total_without_tax: this.getTotalTaxExcluded(),
                total_tax: this.getTax(),
                total_paid: this.getPaidTotal(),
                total_discount: this.getDiscountTotal(),
                tax_details: this.getTaxDetails(),
                change: this.getChange(),
                advans: this.getPaidAdvance(),
                name : this.getName(),
                client: client ? client.name : null ,
                invoice_id: null,   //TODO
                cashier: cashier ? cashier.name : null,
                header: this.pos.config.receipt_header || '',
                footer: this.pos.config.receipt_footer || '',
                precision: {
                    price: 2,
                    money: 2,
                    quantity: 3,
                },
                date: { 
                    year: date.getFullYear(), 
                    month: date.getMonth(), 
                    date: date.getDate(),       // day of the month 
                    day: date.getDay(),         // day of the week 
                    hour: date.getHours(), 
                    minute: date.getMinutes() ,
                    isostring: date.toISOString(),
                    localestring: date.toLocaleString(),
                }, 
                company:{
                    email: company.email,
                    website: company.website,
                    company_registry: company.company_registry,
                    contact_address: company.partner_id[1], 
                    vat: company.vat,
                    name: company.name,
                    phone: company.phone,
                    logo:  this.pos.company_logo_base64,
                },
                shop:{
                    name: shop.name,
                },
                currency: this.pos.currency,
            };
        },
        export_as_JSON: function() {
            var orderLines, paymentLines;
            orderLines = [];
            (this.get('orderLines')).each(_.bind( function(item) {
                return orderLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            paymentLines = [];
            (this.get('paymentLines')).each(_.bind( function(item) {
                return paymentLines.push([0, 0, item.export_as_JSON()]);
            }, this));
            return {
                name: this.getName(),
                amount_paid: this.getPaidTotal(),
                amount_total: this.getTotalTaxIncluded(),
                amount_tax: this.getTax(),
                amount_return: this.getChange(),
                amount_advans: this.getPaidAdvance(),
                po_state: this.get_order_state(),
                order_id: this.get_order_id(),
                order_ids: this.get_order_ids(),
                lines: orderLines,
                statement_ids: paymentLines,
                pos_session_id: this.pos.pos_session.id,
                partner_id: this.get_client() ? this.get_client().id : false,
                user_id: this.pos.cashier ? this.pos.cashier.id : this.pos.user.id,
                uid: this.uid,
                sequence_number: this.sequence_number,
            };
        },
        getSelectedLine: function(){
            return this.selected_orderline;
        },
        selectLine: function(line){
            if(line){
                if(line !== this.selected_orderline){
                    if(this.selected_orderline){
                        this.selected_orderline.set_selected(false);
                    }
                    this.selected_orderline = line;
                    this.selected_orderline.set_selected(true);
                }
            }else{
                this.selected_orderline = undefined;
            }
        },
        deselectLine: function(){
            if(this.selected_orderline){
                this.selected_orderline.set_selected(false);
                this.selected_orderline = undefined;
            }
        },
        selectPaymentline: function(line){
            if(line !== this.selected_paymentline){
                if(this.selected_paymentline){
                    this.selected_paymentline.set_selected(false);
                }
                this.selected_paymentline = line;
                if(this.selected_paymentline){
                    this.selected_paymentline.set_selected(true);
                }
                this.trigger('change:selected_paymentline',this.selected_paymentline);
            }
        },
    });

    module.OrderCollection = Backbone.Collection.extend({
        model: module.Order,
    });

    module.TaxesEngine = instance.web.Class.extend({
        /**
         * @param options
         */
        init: function (options) {
            options = options || {};
            this.pos = options.pos;
            this.db = options.db;
            this.pos_widget = options.pos_widget;
        },
        compute_all: function(taxes, price_unit, force_tax_include) {
            var self = this;
            var res = [];
            var currency_rounding = this.pos.currency.rounding;
            var tax_include = force_tax_include || false;
            if (this.pos.company.tax_calculation_rounding_method == "round_globally"){
               currency_rounding = currency_rounding * 0.00001;
            }
            var base = price_unit;
            _(taxes).each(function(tax) {
                if (tax.price_include || tax_include) {
                    if (tax.type === "percent") {
                        tmp =  round_pr(base - round_pr(base / (1 + tax.amount),currency_rounding),currency_rounding);
                        data = {amount:tmp, price_include:true, id: tax.id};
                        res.push(data);
                    } else if (tax.type === "fixed") {
                        tmp = tax.amount * self.get_quantity();
                        data = {amount:tmp, price_include:true, id: tax.id};
                        res.push(data);
                    } else {
                        throw "This type of tax is not supported by the point of sale: " + tax.type;
                    }
                } else {
                    if (tax.type === "percent") {
                        tmp = round_pr(tax.amount * base, currency_rounding);
                        data = {amount:tmp, price_include:false, id: tax.id};
                        res.push(data);
                    } else if (tax.type === "fixed") {
                        tmp = tax.amount * self.get_quantity();
                        data = {amount:tmp, price_include:false, id: tax.id};
                        res.push(data);
                    } else {
                        throw "This type of tax is not supported by the point of sale: " + tax.type;
                    }

                    var base_amount = data.amount;
                    var child_amount = 0.0;
                    if (tax.child_depend) {
                        res.pop(); // do not use parent tax
                        child_tax = self.compute_all(tax.child_taxes, base_amount);
                        res.push(child_tax);
                        _(child_tax).each(function(child) {
                            child_amount += child.amount;
                        });
                    }
                    if (tax.include_base_amount) {
                        base += base_amount + child_amount;
                    }
                }
            });
            return res;
        },
        get_all_prices: function(options){
            if (arguments.length > 0){
                var qty = options.quantity;
                var unit_price = options.unit_price;
                var discount = options.disc;
                var tax_included = typeof options.force_tax_included === 'undefined' && false || options.force_tax_included;
                var product =  options.product;
                //var product =  this.get_product();
            } else {
                return false;
            }
            var base = round_pr(qty * unit_price * (1.0 - (discount / 100.0)), this.pos.currency.rounding);
            var totalTax = base;
            var totalNoTax = base;
            var taxtotal = 0;


            var taxes_ids = product.taxes_id;
            var taxes =  this.pos.taxes;
            var taxdetail = {};
            var product_taxes = [];

            _(taxes_ids).each(function(el){
                product_taxes.push(_.detect(taxes, function(t){
                    return t.id === el;
                }));
            });

            var all_taxes = _(this.compute_all(product_taxes, base, tax_included)).flatten();

            _(all_taxes).each(function(tax) {
                if (tax.price_include) {
                    totalNoTax -= tax.amount;
                } else {
                    totalTax += tax.amount;
                }
                taxtotal += tax.amount;
                taxdetail[tax.id] = tax.amount;
            });
            totalNoTax = round_pr(totalNoTax, this.pos.currency.rounding);

            return {
                "priceWithTax": totalTax,
                "priceWithoutTax": totalNoTax,
                "tax": taxtotal,
                "taxDetails": taxdetail,
                "tax_included": tax_included,
            };
        },
    });

    /**
     * Pricelist Engine to compute price
     */
    module.PricelistEngine = instance.web.Class.extend({
        /**
         * @param options
         */
        init: function (options) {
            options = options || {};
            this.pos = options.pos;
            this.db = options.db;
            this.pos_widget = options.pos_widget;
            //console.log("Price List Engine", this);
        },
        /**
         * compute price for all price list
         * @param db
         * @param product
         * @param partner
         * @param qty
         * @returns {*}
         */
        compute_price_all: function (db, product, partner, qty) {
            var price_list_id = false;
            if (partner && partner.property_product_pricelist) {
                price_list_id = partner.property_product_pricelist[0];
            } else {
                price_list_id = this.pos.config.pricelist_id[0];
            }
            return this.compute_price(db, product, partner, qty, parseInt(price_list_id));
        },
        /**
         * loop find a valid version for the price list id given in param
         * @param db
         * @param pricelist_id
         * @returns {boolean}
         */
        find_valid_pricelist_version: function (db, pricelist_id) {
            var date = new Date();
            var version = false;
            var pricelist = db.pricelist_by_id[pricelist_id];
            //console.log("find_valid_pricelist_version", pricelist, db.pricelist_by_id, pricelist_id);
            for (var i = 0, len = pricelist.version_id.length; i < len; i++) {
                var v = db.pricelist_version_by_id[pricelist.version_id[i]];
                if (((v.date_start == false)
                    || (new Date(v.date_start) <= date)) &&
                    ((v.date_end == false)
                    || (new Date(v.date_end) >= date))) {
                    version = v;
                    break;
                }
            }
            return version;
        },
        /**
         * compute the price for the given product
         * @param database
         * @param product
         * @param partner
         * @param qty
         * @param pricelist_id
         * @returns {boolean}
         */
        compute_price: function (database, product, partner, qty, pricelist_id) {
            var self = this;
            var db = database;

            // get a valid version
            var version = this.find_valid_pricelist_version(db, pricelist_id);
            if (version == false) {
                self.pos_widget.screen_messages.errors('pricelist-no-active');
                return false;
            }

            // prepare filters
            // get categories
            var categ_ids = [];
            if (product.categ_id) {
                categ_ids.push(product.categ_id[0]);
                categ_ids = categ_ids.concat(
                    db.product_category_ancestors[product.categ_id[0]]
                );
            }
            // get templatess
            var prod_tmpl_ids = [product.product_tmpl_id];
            // get products ids
            var prod_ids = [product.id];
            // get margin clasifications
            var mc_ids = [];
            if(db.template_by_id[product.product_tmpl_id].margin_classification_id !== false){
                var mc_ids = [db.template_by_id[product.product_tmpl_id].margin_classification_id[0]];
            }
            // find items
            var items = [], i, len;
            for (i = 0, len = db.pricelist_item_sorted.length; i < len; i++) {
                var item = db.pricelist_item_sorted[i];
                if ((item.product_tmpl_id === false
                    || prod_tmpl_ids.indexOf(item.product_tmpl_id[0]) != -1) &&
                    (item.product_id === false
                    || prod_ids.indexOf(item.product_id[0]) !== -1) &&
                    (item.categ_id === false
                    || categ_ids.indexOf(item.categ_id[0]) !== -1) &&
                    (item.margin_classification_id === false
                    || mc_ids.indexOf(item.margin_classification_id[0]) !== -1) &&
                    (item.price_version_id[0] === version.id)) {
                    items.push(item);
                }
            }

            var results = {};
            results[product.id] = 0.0;
            var price_types = {};
            var price = false;
            //console.log("Rules", version, partner, db.pricelist_item_sorted, items, db.template_by_id[product.product_tmpl_id].margin_classification_id);
            // loop through items
            for (i = 0, len = items.length; i < len; i++) {
                var rule = items[i];

                if (rule.min_quantity && qty < rule.min_quantity) {
                    continue;
                }
                if (rule.product_id && rule.product_id[0]
                    && product.id != rule.product_id[0]) {
                    continue;
                }
                if (rule.product_tmpl_id && rule.product_tmpl_id[0]
                    && product.product_tmpl_id != rule.product_tmpl_id[0]) {
                    continue;
                }
                if (rule.categ_id) {
                    var cat_id = product.categ_id[0];
                    while (cat_id) {
                        if (cat_id == rule.categ_id[0]) {
                            break;
                        }
                        cat_id = db.product_category_by_id[cat_id].parent_id[0]
                    }
                    if (!(cat_id)) {
                        continue;
                    }
                }
                if (rule.margin_classification_id && rule.margin_classification_id[0]
                    && db.template_by_id[product.product_tmpl_id].margin_classification_id[0] != rule.margin_classification_id[0]) {
                        continue;
                }
                // Based on field
                switch (rule.base) {
                    case -1:
                        if (rule.base_pricelist_id) {
                            price = self.compute_price(
                                db, product, false, qty,
                                rule.base_pricelist_id[0]
                            );
                        }
                        break;
                    case -2:
                        var seller = false;
                        for (var index in product.seller_ids) {
                            var seller_id = product.seller_ids[index];
                            var _tmp_seller = db.supplierinfo_by_id[seller_id];
                            if ((!partner) || (_tmp_seller.name.length
                                && _tmp_seller.name[0] != partner.name))
                                continue;
                            seller = _tmp_seller
                        }
                        if (!seller && product.seller_ids) {
                            seller =
                                db.supplierinfo_by_id[product.seller_ids[0]];
                        }
                        if (seller) {
                            for (var _id in seller.pricelist_ids) {
                                var info_id = seller.pricelist_ids[_id];
                                var line =
                                    db.pricelist_partnerinfo_by_id[info_id];
                                if (line.min_quantity <= qty) {
                                    price = line.price
                                }
                            }
                        }
                        break;
                    default:
                        if (!price_types.hasOwnProperty(rule.base)) {
                            price_types[rule.base] =
                                db.product_price_type_by_id[rule.base];
                        }
                        var price_type = price_types[rule.base];
                        if (db.product_by_id[product.id]
                                .hasOwnProperty(price_type.field)) {
                            price =
                                db.product_by_id[product.id][price_type.field];
                        }
                }
                if (price !== false) {
                    var price_limit = price;
                    price = price * (1.0 + (rule['price_discount']
                            ? rule['price_discount']
                            : 0.0));
                    if (rule['price_round']) {
                        price = parseFloat(price.toFixed(
                                Math.ceil(Math.log(1.0 / rule['price_round'])
                                    / Math.log(10)))
                        );
                    }
                    price += (rule['price_surcharge']
                        ? rule['price_surcharge']
                        : 0.0);
                    if (rule['price_min_margin']) {
                        price = Math.max(
                            price, price_limit + rule['price_min_margin']
                        )
                    }
                    if (rule['price_max_margin']) {
                        price = Math.min(
                            price, price_limit + rule['price_min_margin']
                        )
                    }
                }
                break;
            }
            return price
        },
        update_products_prices: function(product, partner, db) {
            db = db || this.db;
            var rules = db.find_product_rules(product);
            var quantities = [];
            quantities.push(1);
            for (var j = 0; j < rules.length; j++) {
                if ($.inArray(rules[j].min_quantity, quantities) === -1) {
                    quantities.push(rules[j].min_quantity);
                }
            }
            quantities = quantities.sort();
            var lst_price = round_di(product.lst_price, this.pos.dp['Product Price']);
            var prices_tooltip = '';
            var price_display = 0;
            for (var k = 0; k < quantities.length; k++) {
                var qty = quantities[k];
                var price = this.compute_price_all(db, product, partner, qty);
                var priceobj = {price: price, tax_included: false};
                if (price !== false) {
                    var priceobj = this.pos.taxes_engine.get_all_prices({quantity: qty, unit_price: price, disc: 0, force_tax_included: false, product: product,});
                    price = priceobj.priceWithTax;
                    price = round_di(price, this.pos.dp['Product Price']);
                    if (k == 0) {
                        price_display = price;
                    }
                    price = this.pos_widget.format_currency(price, 'Product Price');
                    prices_tooltip += qty + 'x &#8594; ' + price + '<br/>';
                }
            }
            return {lst_price: lst_price, price: price_display, tooltip: prices_tooltip, discount: (Math.abs(lst_price - price_display) > 0.001), priceWithoutTax: priceobj.priceWithoutTax};
        },
        /**
         * @param partner
         */
        update_products_ui: function(partner) {
            var db = this.db;
            if (!this.pos_widget || !this.pos_widget.product_screen) return;
            var product_list_ui = this.pos_widget.product_screen.$('.product-list span.product');
            for (var i = 0, len = product_list_ui.length; i < len; i++) {
                var product_ui = product_list_ui[i];
                var product_id = $(product_ui).data('product-id');
                var product = $.extend({}, db.get_product_by_id(product_id));
                var price = this.update_products_prices(product, partner, db);
                //console.log("Prices", product.lst_price, price.price);
                $(product_ui).find('.price-tag').html(this.pos_widget.format_currency(price.price, 'Product Price'));
                if(!_.isEmpty(product.min_qty)){
                    $(product_ui).find('.qty-tag').html(product.min_qty);
                }
                if (price.tooltip != '') {
                    price.tooltip = '[' + product.default_code + '] ' + product.display_name + '(' + this.pos_widget.format_currency(product.lst_price, 'Product Price') + ') ' + price.tooltip;
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
                if (price.lst_price - product.standart_price <= 0.0){
                    $(product_ui).find('.price-tag').addClass('wrong');
                    $(product_ui).find('.qty-tag').addClass('wrong');
                } else if(Math.abs(product.lst_price - price.price) > 0.001){
                    $(product_ui).find('.price-tag').addClass('discount');
                    $(product_ui).find('.qty-tag').addClass('discount');
                } else {
                    $(product_ui).find('.price-tag').removeClass('discount');
                    $(product_ui).find('.qty-tag').removeClass('discount');
                }
            }
        },
        /**
         *
         * @param partner
         * @param orderLines
         */
        update_ticket: function (partner, orderLines) {
            var db = this.db;
            for (var i = 0, len = orderLines.length; i < len; i++) {
                var line = orderLines[i];
                var product = line.product;
                var quantity = line.quantity;
                var price = this.compute_price_all(
                    db, product, partner, quantity
                );
                if (price !== false) {
                    line.price = price;
                }
                line.trigger('change', line);
            }
        }
    });

    /*
     The numpad handles both the choice of the property currently being modified
     (quantity, price or discount) and the edition of the corresponding numeric value.
     */
    module.NumpadState = Backbone.Model.extend({
        defaults: {
            buffer: "0",
            mode: "quantity"
        },
        appendNewDecimalChar: function(newChar) {
            var oldBuffer;
            oldBuffer = this.get('buffer');
            if (oldBuffer === '0') {
                this.set({
                    buffer: newChar.replace('+','')
                });
            } else if (oldBuffer === '-0') {
                this.set({
                    buffer: "-" + newChar.replace('+','')
                });
            } else {
                this.set({
                    buffer: math.eval((this.get('buffer')) + newChar).toString()
                });
            }
            this.trigger('set_value',this.get('buffer'));
        },
        appendNewChar: function(newChar) {
            var oldBuffer;
            oldBuffer = this.get('buffer');
            if (oldBuffer === '0') {
                this.set({
                    buffer: newChar
                });
            } else if (oldBuffer === '-0') {
                this.set({
                    buffer: "-" + newChar
                });
            } else {
                this.set({
                    buffer: (this.get('buffer')) + newChar
                });
            }
            this.trigger('set_value',this.get('buffer'));
        },
        deleteLastChar: function() {
            if(this.get('buffer') === ""){
                if(this.get('mode') === 'quantity'){
                    this.trigger('set_value','remove');
                }else{
                    this.trigger('set_value',this.get('buffer'));
                }
            }else{
                var newBuffer = this.get('buffer').slice(0,-1) || "";
                this.set({ buffer: newBuffer });
                this.trigger('set_value',this.get('buffer'));
            }
        },
        switchSign: function() {
            var oldBuffer;
            oldBuffer = this.get('buffer');
            this.set({
                buffer: oldBuffer[0] === '-' ? oldBuffer.substr(1) : "-" + oldBuffer 
            });
            this.trigger('set_value',this.get('buffer'));
        },
        changeMode: function(newMode) {
            this.set({
                buffer: "0",
                mode: newMode
            });
        },
        reset: function() {
            this.set({
                buffer: "0",
                mode: "quantity"
            });
        },
        resetValue: function(){
            this.set({buffer:'0'});
        },
    });
}
