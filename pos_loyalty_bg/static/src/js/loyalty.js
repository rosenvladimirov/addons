/******************************************************************************
*    Point Of Sale - Pricelist for POS Odoo
*    Copyright (C) 2014 Taktik (http://www.taktik.be)
*    @author Rosen Vladimirov <vladimirov.rosen@gmail.com>
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Affero General Public License as
*    published by the Free Software Foundation, either version 3 of the
*    License, or (at your option) any later version.
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Affero General Public License for more details.
*    You should have received a copy of the GNU Affero General Public License
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
******************************************************************************/
openerp.pos_loyalty_bg = function(instance) {
    var module = instance.point_of_sale;
    var _t = instance.web._t;
    var QWeb = instance.web.qweb;
    var round_pr = instance.web.round_precision;
    var round_di = instance.web.round_decimals;

    var _super_PosModel = module.PosModel;
    module.PosModel = module.PosModel.extend({
        initialize: function(session, attributes) {
            _super_PosModel.prototype.initialize.apply(this, arguments);
            console.log('Loyalty Programs-add models',arguments);
            var partner_model = _.find(_super_PosModel.prototype.models,function(model){ return model.model === 'res.partner'; });
            partner_model.fields.push('loyalty_points');
            console.log('Loyalty Programs-add field in partner_model',_super_PosModel.prototype.models.map(function (model) { return model.model; }).indexOf('account.journal'));
            var partner_model_index = _super_PosModel.prototype.models.map(function (model) { return model.model; }).indexOf('account.journal');
            console.log('Loyalty Programs-add field in product_pricelist_index',partner_model_index);

            _super_PosModel.prototype.models.splice(++partner_model_index, 0,
                {
                model: 'loyalty.program',
                condition: function(self){ return !!self.config.loyalty_id[0]; },
                fields: ['name','pp_currency','pp_product','pp_order','rounding'],
                domain: null,
                //domain: function(self){ return [['id','=',self.config.loyalty_id[0]]]; },
                loaded: function(self,loyalties){
                    self.loyalty = loyalties[0] || {};
                    //self.db.add_loyalties(loyalties);
                    console.log('Loyalty Programs->',self.loyalty);
                    },
                },{
                model: 'loyalty.rule',
                condition: function(self){ return !!self.loyalty; },
                fields: ['name','type','product_id','category_id','cumulative','sequence','pp_product','pp_currency'],
                domain: function(self){ return [['loyalty_program_id','=',self.loyalty.id]]; },
                loaded: function(self,rules){

                    self.loyalty.rules = rules || {};
                    //self.db.add_rules(rules);
                    self.loyalty.rules.sort(function(a, b){return a['sequence']-b['sequence']});
                    self.loyalty.rules_by_product_id = {};
                    self.loyalty.rules_by_category_id = {};
                    console.log('Loyalty Rules',self.loyalty.rules);

                    for (var i = 0; i < rules.length; i++){
                        var rule = rules[i];
                        if (rule.type === 'product') {
                            if (!self.loyalty.rules_by_product_id[rule.product_id[0]]) {
                                self.loyalty.rules_by_product_id[rule.product_id[0]] = [rule];
                            } else if (rule.cumulative) {
                                self.loyalty.rules_by_product_id[rule.product_id[0]].unshift(rule);
                            } else {
                                self.loyalty.rules_by_product_id[rule.product_id[0]].push(rule);
                            }
                        } else if (rule.type === 'category') {
                        var category = self.db.get_category_by_id(rule.category_id[0]);
                        if (!self.loyalty.rules_by_category_id[category.id]) {
                            self.loyalty.rules_by_category_id[category.id] = [rule];
                            } else if (rule.cumulative) {
                            self.loyalty.rules_by_category_id[category.id].unshift(rule);
                            } else {
                            self.loyalty.rules_by_category_id[category.id].push(rule);
                            }
                        }
                    }
                    },
                },{
                model: 'loyalty.reward',
                condition: function(self){ return !!self.loyalty; },
                fields: ['name','type','minimum_points','gift_product_id','point_cost','discount_product_id','discount','point_value','point_product_id'],
                domain: function(self){ return [['loyalty_program_id','=',self.loyalty.id]]; },
                loaded: function(self,rewards){
                    self.loyalty.rewards = rewards || {};
                    //self.db.add_rewards(rewards);
                    self.loyalty.rewards_by_id = {};
                    for (var i = 0; i < rewards.length;i++) {
                        self.loyalty.rewards_by_id[rewards[i].id] = rewards[i];
                        }
                        console.log('Reward',self.loyalty);
                },
            });
        },
        push_order: function(order){
            var self = this;
            var pushed = _super_PosModel.prototype.push_order.call(this, order);
            var client = order && order.get_client();
            if (client){
                client.loyalty_points = order.get('loyalty_points');
            }
            return pushed;
        },
    });

    var _super_Orderline = module.Orderline;
    module.Orderline = module.Orderline.extend({
        initialize: function(session, attributes) {
            _super_Orderline.prototype.initialize.apply(this, arguments);
            //this.fields.push('loyalty_points');
            this.loyalty_program_id = this.pos.loyalty.id;
        },
        get_reward: function(){
            return this.pos.loyalty.rewards_by_id[this.reward_id];
        },
        set_reward: function(reward){
            this.set({
                reward_id: reward.id,
            });
        },
        set_loyalty_program: function(program_id){
            this.set({
                loyalty_program_id: program_id,
            });
        },
        export_as_JSON: function(){
            var json = _super_Orderline.prototype.export_as_JSON.apply(this,arguments);
            json.reward_id = this.reward_id;
            return json;
        },
        init_from_JSON: function(json){
            _super_Orderline.prototype.init_from_JSON.apply(this,arguments);
            this.reward_id = json.reward_id;
        },
    });

    var _super = module.Order;
    module.Order = module.Order.extend({
//        initialize: function(session, attributes) {
//            _super.prototype.initialize.apply(this, arguments);
//            this.fields.push('loyalty_program_id');
//            this.fields.push('loyalty_points');
//        },
        /* The total of points won, excluding the points spent on rewards */
        get_won_points: function(){

            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            }

            var orderLines = this.get_orderlines();
            var rounding   = this.pos.loyalty.rounding;

            var product_sold = 0;
            var total_sold   = 0;
            var total_points = 0;

            for (var i = 0; i < orderLines.length; i++) {
                var line = orderLines[i];
                var product = line.get_product();
                var rules  = this.pos.loyalty.rules_by_product_id[product.id] || [];
                var overriden = false;

                if (line.get_reward()) {  // Reward products are ignored
                    continue;
                }

                for (var j = 0; j < rules.length; j++) {
                    var rule = rules[j];
                    total_points += round_pr(line.get_quantity() * rule.pp_product, rounding);
                    total_points += round_pr(line.get_price_with_tax() * rule.pp_currency, rounding);
                    line.set_loyalty_program(this.pos.loyalty.id);
                    // if affected by a non cumulative rule, skip the others. (non cumulative rules are put
                    // at the beginning of the list when they are loaded )
                    if (!rule.cumulative) {
                        overriden = true;
                        break;
                    }
                }

                // Test the category rules
                if ( product.pos_categ_id ) {
                    var category = this.pos.db.get_category_by_id(product.pos_categ_id[0]);
                    while (category && !overriden) {
                        var rules = this.pos.loyalty.rules_by_category_id[category.id] || [];
                        for (var j = 0; j < rules.length; j++) {
                            var rule = rules[j];
                            total_points += round_pr(line.get_quantity() * rule.pp_product, rounding);
                            total_points += round_pr(line.get_price_with_tax() * rule.pp_currency, rounding);
                            if (!rule.cumulative) {
                                overriden = true;
                                break;
                            }
                        }
                        var _category = category;
                        category = this.pos.db.get_category_by_id(this.pos.db.get_category_parent_id(category.id));
                        if (_category === category) {
                            break;
                        }
                    }
                }

                if (!overriden) {
                    product_sold += line.get_quantity();
                    total_sold   += line.get_price_with_tax();
                }
            }

            total_points += round_pr( total_sold * this.pos.loyalty.pp_currency, rounding );
            total_points += round_pr( product_sold * this.pos.loyalty.pp_product, rounding );
            total_points += round_pr( this.pos.loyalty.pp_order, rounding );

            return total_points;
        },

        /* The total number of points spent on rewards */
        get_spent_points: function() {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            } else {
                var lines    = this.get_orderlines();
                var rounding = this.pos.loyalty.rounding;
                var points   = 0;

                for (var i = 0; i < lines.length; i++) {
                    var line = lines[i];
                    var reward = line.get_reward();
                    if (reward) {
                        if (reward.type === 'gift') {
                            points += round_pr(line.get_quantity() * reward.point_cost, rounding);
                        } else if (reward.type === 'discount') {
                            points += round_pr(-line.get_display_price() * reward.point_cost, rounding);
                        } else if (reward.type === 'resale') {
                            points += (-line.get_quantity());
                        }
                    }
                }

                return points;
            }
        },

        /* The total number of points lost or won after the order is validated */
        get_new_points: function() {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.get_won_points() - this.get_spent_points(), this.pos.loyalty.rounding);
            }
        },

        /* The total number of points that the customer will have after this order is validated */
        get_new_total_points: function() {
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.get_client().loyalty_points + this.get_new_points(), this.pos.loyalty.rounding);
            }
        },

        /* The number of loyalty points currently owned by the customer */
        get_current_points: function(){
            return this.get_client() ? this.get_client().loyalty_points : 0;
        },

        /* The total number of points spendable on rewards */
        get_spendable_points: function(){
            if (!this.pos.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.get_client().loyalty_points - this.get_spent_points(), this.pos.loyalty.rounding);
            }
        },

        /* The list of rewards that the current customer can get */
        get_available_rewards: function(){
            var client = this.get_client();
            if (!client) {
                return [];
            }

            var rewards = [];
            for (var i = 0; i < this.pos.loyalty.rewards.length; i++) {
                var reward = this.pos.loyalty.rewards[i];
                if (reward.minimum_points > this.get_spendable_points()) {
                    continue;
                } else if(reward.type === 'gift' && reward.point_cost > this.get_spendable_points()) {
                    continue;
                }
                rewards.push(reward);
            }
            return rewards;
        },

        apply_reward: function(reward){
            var client = this.get_client();
            if (!client) {
                return;
            } else if (reward.type === 'gift') {
                var product = this.pos.db.get_product_by_id(reward.gift_product_id[0]);

                if (!product) {
                    return;
                }

                var line = this.add_product(product, {
                    price: 0,
                    quantity: 1,
                    merge: false,
                    extras: { reward_id: reward.id },
                });

            } else if (reward.type === 'discount') {

                var lrounding = this.pos.loyalty.rounding;
                var crounding = this.pos.currency.rounding;
                var spendable = this.get_spendable_points();
                var order_total = this.get_total_with_tax();
                var discount    = round_pr(order_total * reward.discount,crounding);

                if ( round_pr(discount * reward.point_cost,lrounding) > spendable ) {
                    discount = round_pr(Math.floor( spendable / reward.point_cost ), crounding);
                }

                var product   = this.pos.db.get_product_by_id(reward.discount_product_id[0]);

                if (!product) {
                    return;
                }

                var line = this.add_product(product, {
                    price: -discount,
                    quantity: 1,
                    merge: false,
                    extras: { reward_id: reward.id },
                });

            } else if (reward.type === 'resale') {

                var lrounding = this.pos.loyalty.rounding;
                var crounding = this.pos.currency.rounding;
                var spendable = this.get_spendable_points();
                var order_total = this.get_total_with_tax();
                var product = this.pos.db.get_product_by_id(reward.point_product_id[0]);

                if (!product) {
                    return;
                }

                if ( round_pr( spendable * product.price, crounding ) > order_total ) {
                    spendable = round_pr( Math.floor(order_total / product.price), lrounding);
                }

                if ( spendable < 0.00001 ) {
                    return;
                }

                var line = this.add_product(product, {
                    quantity: -spendable,
                    merge: false,
                    extras: { reward_id: reward.id },
                });
            }
        },

        export_for_printing: function(){
            var json = _super.prototype.export_for_printing.apply(this,arguments);
            if (this.pos.loyalty && this.get_client()) {
                json['loyalty'] = {
                    rounding:     this.pos.loyalty.rounding || 1,
                    name:         this.pos.loyalty.name,
                    client:       this.get_client().name,
                    points_won  : this.get_won_points(),
                    points_spent: this.get_spent_points(),
                    points_total: this.get_new_total_points(),
                };
            }
            return json;
        },

        export_as_JSON: function(){
            var json = _super.prototype.export_as_JSON.apply(this,arguments);
            json.loyalty_points = this.get_new_points();
            json.loyalty_program_id = self.loyalty.id;
            return json;
        },
    });

  module.LoyaltyButton = module.ActionButtonWidget.extend({
    template: 'LoyaltyButton',
    button_click: function(){
        var self = this;
        var order  = this.pos.get_order();
        var client = order.get_client();
        if (!client) {
            this.gui.show_screen('clientlist');
            return;
        }

        var rewards = order.get_available_rewards();
        if (rewards.length === 0) {
            this.gui.show_popup('error',{
                'title': 'No Rewards Available',
                'body':  'There are no rewards available for this customer as part of the loyalty program',
            });
            return;
        } else if (rewards.length === 1 && this.pos.loyalty.rewards.length === 1) {
            order.apply_reward(rewards[0]);
            return;
        } else {
            var list = [];
            for (var i = 0; i < rewards.length; i++) {
                list.push({
                    label: rewards[i].name,
                    item:  rewards[i],
                });
            }
            this.gui.show_popup('selection',{
                'title': 'Please select a reward',
                'list': list,
                'confirm': function(reward){
                    order.apply_reward(reward);
                },
            });
        }
    },
  });

  module.LoyaltyButton = module.PosBaseWidget.extend({
        template: 'LoyaltyButton',

        renderElement: function() {
            var self = this;
            this._super();
            this.$el.click(function(){
                return this.pos.loyalty && this.pos.loyalty.rewards.length;
            });
    },
  });

  module.OrderWidget.include({
    update_summary: function(){
        this._super();

        var order = this.pos.get_order('selectedOrder');

        var $loypoints = $(this.el).find('.summary .loyalty-points');

        if(this.pos.loyalty && order.get_client()){
            var points_won      = order.get_won_points();
            var points_spent    = order.get_spent_points();
            var points_total    = order.get_new_total_points();
            $loypoints.replaceWith($(QWeb.render('LoyaltyPoints',{
                widget: this,
                rounding: this.pos.loyalty.rounding,
                points_won: points_won,
                points_spent: points_spent,
                points_total: points_total,
            })));
            $loypoints = $(this.el).find('.summary .loyalty-points');
            $loypoints.removeClass('oe_hidden');

            if(points_total < 0){
                $loypoints.addClass('negative');
            }else{
                $loypoints.removeClass('negative');
            }
        }else{
            $loypoints.empty();
            $loypoints.addClass('oe_hidden');
        }

        if (this.pos.loyalty &&
            order.get_client() &&
            this.getParent().action_buttons &&
            this.getParent().action_buttons.loyalty) {

            var rewards = order.get_available_rewards();
            this.getParent().action_buttons.loyalty.highlight(!!rewards.length);
        }
    },
  });
}
