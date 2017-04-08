/******************************************************************************
*    Point Of Sale - Pricelist for POS Odoo
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

function pos_loyalty_bg_models(instance, module) {
    var _t = instance.web._t;
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
                //domain: null,
                domain: function(self){ return [['id','=',self.config.loyalty_id[0]]]; },
                loaded: function(self,loyalties){
                    self.db.add_loyalty(loyalties);
                    console.log('Loyalty Programs->',self.db.loyalty);
                    },
                },{
                model: 'loyalty.rule',
                condition: function(self){ return !!self.db.loyalty; },
                fields: ['name','type','product_id','category_id','cumulative','sequence','pp_product','pp_currency'],
                domain: function(self){ return [['loyalty_program_id','=',self.db.loyalty.id]]; },
                loaded: function(self,rules){
                    self.db.add_rules(rules);
                    console.log('Loyalty Rules',self.db.loyalty.rules);
                    },
                },{
                model: 'loyalty.reward',
                condition: function(self){ return !!self.db.loyalty; },
                fields: ['name','type','minimum_points','gift_product_id','point_cost','discount_product_id','discount','point_value','point_product_id'],
                domain: function(self){ return [['loyalty_program_id','=',self.db.loyalty.id]]; },
                loaded: function(self,rewards){
                    self.db.add_rewards(rewards);
                    console.log('Reward',self.db.loyalty);
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
        //initialize: function(session, attributes) {
        //    _super_Orderline.prototype.initialize.apply(this, arguments);
        //    this.loyalty_program_id = false;
        //    this.loyalty_points = 0;
            //this.fields.push('loyalty_points');
            //this.loyalty_program_id = this.pos.loyalty.id;
        //},
        get_reward: function(){
            return this.pos.db.loyalty.rewards_by_id[this.reward_id];
        },
        set_reward: function(reward){
            this.reward_id = reward.id;
        },
        set_loyalty_points: function(loyalty_points){
            this.loyalty_points = loyalty_points;
        },
        export_as_JSON: function(){
            var json = _super_Orderline.prototype.export_as_JSON.apply(this,arguments);
            new_val = {
                reward_id: this.reward_id;
                loyalty_points: this.loyalty_points;
            }
            $.extend(json, new_val);
            return json;
        },
        init_from_JSON: function(json){
            _super_Orderline.prototype.init_from_JSON.apply(this,arguments);
            this.reward_id = json.reward_id;
            this.loyalty_points = json.loyalty_points;
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
        set_loyalty_program: function(program_id){
            this.loyalty_program_id = program_id;
        },
        get_won_points: function(){
            console.log("Won points start", this.pos.db.loyalty);
            if (!this.pos.db.loyalty || !this.get_client()) {
                return 0;
            }

            //var orderLines = this.get_orderlines();
            var rounding   = this.pos.db.loyalty.rounding;

            var product_sold = 0;
            var total_sold   = 0;
            var total_points = 0;
            var orderLines = [];
            if (this.get('orderLines').models !== undefined) {
                orderLines = this.get('orderLines').models;
            }
            for (var i = 0; i < orderLines.length; i++) {
                var line = orderLines[i];
                var product = line.get_product();
                var rules  = this.pos.db.loyalty.rules_by_product_id[product.id] || [];
                var overriden = false;
                var sub_total_points = 0;

                if (line.get_reward()) {  // Reward products are ignored
                    continue;
                }
                for (var j = 0; j < rules.length; j++) {
                    var rule = rules[j];
                    total_points += round_pr(line.get_quantity() * rule.pp_product, rounding);
                    total_points += round_pr(line.get_price_with_tax() * rule.pp_currency, rounding);
                    // if affected by a non cumulative rule, skip the others. (non cumulative rules are put
                    // at the beginning of the list when they are loaded )
                    if (!rule.cumulative) {
                        overriden = true;
                        break;
                    }
                }
                // Test the category rules
                if ( product.categ_id ) {
                    var category = this.pos.db.get_category_by_id(product.categ_id[0]);
                    while (category && !overriden) {
                        var rules = this.pos.db.loyalty.rules_by_category_id[category.id] || [];
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
                        category = this.pos.db.get_category_by_id(this.pos.get_category_parent_id(category.id));
                        if (_category === category) {
                            break;
                        }
                    }
                }

                if (!overriden) {
                    product_sold += line.get_quantity();
                    total_sold   += line.get_price_with_tax();
                }
                sub_total_points += round_pr( total_sold * this.pos.db.loyalty.pp_currency, rounding );
                sub_total_points += round_pr( product_sold * this.pos.db.loyalty.pp_product, rounding );
                sub_total_points += round_pr( this.pos.db.loyalty.pp_order, rounding );
                console.log("Won points",orderLines[i]);

                line.set_loyalty_points(sub_total_points); // decorate orderlines wth middle subtotal points
            }

            total_points += round_pr( total_sold * this.pos.db.loyalty.pp_currency, rounding );
            total_points += round_pr( product_sold * this.pos.db.loyalty.pp_product, rounding );
            total_points += round_pr( this.pos.db.loyalty.pp_order, rounding );
            if (total_points != 0){this.set_loyalty_program(this.pos.db.loyalty.id);}; // decorate lines with loyalty program id
            return total_points;
        },

        /* The total number of points spent on rewards */
        get_spent_points: function() {
            if (!this.pos.db.loyalty || !this.get_client()) {
                return 0;
            } else {
                //var lines    = this.get_orderlines();
                var rounding = this.pos.db.loyalty.rounding;
                var points   = 0;
                var orderLines = [];
                if (this.get('orderLines').models !== undefined) {
                    orderLines = this.get('orderLines').models;
                }

                for (var i = 0; i < orderLines.length; i++) {
                    var line = orderLines[i];
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
                if (points != 0){this.set_loyalty_program(this.pos.db.loyalty.id);}; // decorate lines with loyalty program id
                return points;
            }
        },

        /* The total number of points lost or won after the order is validated */
        get_new_points: function() {
            console.log('Get new points', this.pos.db.loyalty);
            if (!this.pos.db.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.get_won_points() - this.get_spent_points(), this.pos.db.loyalty.rounding);
            }
        },

        /* The total number of points that the customer will have after this order is validated */
        get_new_total_points: function() {
            if (!this.pos.db.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.get_client().loyalty_points + this.get_new_points(), this.pos.db.loyalty.rounding);
            }
        },

        /* The number of loyalty points currently owned by the customer */
        get_current_points: function(){
            return this.get_client() ? this.get_client().loyalty_points : 0;
        },

        /* The total number of points spendable on rewards */
        get_spendable_points: function(){
            if (!this.pos.db.loyalty || !this.get_client()) {
                return 0;
            } else {
                return round_pr(this.get_client().loyalty_points - this.get_spent_points(), this.pos.db.loyalty.rounding);
            }
        },

        /* The list of rewards that the current customer can get */
        get_available_rewards: function(){
            var client = this.get_client();
            if (!client) {
                return [];
            }

            var rewards = [];
            for (var i = 0; i < this.pos.db.loyalty.rewards.length; i++) {
                var reward = this.pos.db.loyalty.rewards[i];
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
                var product = this.db.get_product_by_id(reward.gift_product_id[0]);

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

                var lrounding = this.pos.db.loyalty.rounding;
                var crounding = this.pos.currency.rounding;
                var spendable = this.get_spendable_points();
                var order_total = this.get_total_with_tax();
                var discount    = round_pr(order_total * reward.discount,crounding);

                if ( round_pr(discount * reward.point_cost,lrounding) > spendable ) {
                    discount = round_pr(Math.floor( spendable / reward.point_cost ), crounding);
                }

                var product   = this.pos.get_product_by_id(reward.discount_product_id[0]);

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

                var lrounding = this.pos.db.loyalty.rounding;
                var crounding = this.pos.currency.rounding;
                var spendable = this.get_spendable_points();
                var order_total = this.get_total_with_tax();
                var product = this.db.get_product_by_id(reward.point_product_id[0]);

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
            if (this.pos.db.loyalty && this.get_client()) {
                json['loyalty'] = {
                    rounding:     this.pos.db.loyalty.rounding || 1,
                    name:         this.pos.db.loyalty.name,
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
            new_val = {
                loyalty_points: this.get_new_points();
                loyalty_program_id: this.loyalty_program_id;
            }
            $.extend(json, new_val);
            //json.loyalty_program_id = self.pos.loyalty.id;
            console.log('Parce order', json);
            return json;
        },
        init_from_JSON: function(json){
            _super.prototype.init_from_JSON.apply(this,arguments);
            this.loyalty_points = json.loyalty_points;
            this.loyalty_program_id = json.loyalty_program_id;
        },
    });
}
