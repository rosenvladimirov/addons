function pos_loyalty_bg_db(instance, module) {

    module.PosDB = module.PosDB.extend({
        init: function (options) {
            options = options || {};
            this._super(options);
            this.loyalty = {};
            this.loyalty.rules = {};
            this.loyalty.rules_by_product_id = {};
            this.loyalty.rules_by_category_id = {};
            this.loyalty.rewards = {};
            this.loyalty.rewards_by_id = {};
            this.loyalty.product_by_reward_id = {};
            this.loyalty.reward_ancestors = {};
            this.loyalty.reward_all_product = {};
        },
        add_loyalty: function(loyalties){
            this.loyalty = loyalties[0] || {};
        },
        add_rules: function(rules){
            this.loyalty.rules = rules || {};
            this.loyalty.rules_by_product_id = {};
            this.loyalty.rules_by_category_id = {};
            rules.sort(function(a, b){return a['sequence']-b['sequence']});
            for (var i = 0; i < rules.length; i++){
                var rule = rules[i];
                //console.log('Loyalty Rule separe ->', rule);
                //console.log('Loyalty Rule is product is array->', (rule.product_id instanceof Array));
                //console.log('Loyalty Rule is category is array->', (rule.category_id instanceof Array));
                //console.log('Loyalty Rule is category->', rule.product_id[0]);
                //console.log('Loyalty Rule is product->', rule.category_id[0]);
                if ((rule.product_id instanceof Array) && rule.category_id == false) {
                    var product = this.get_product_by_id(rule.product_id[0]);
                    console.log('Product get by id', product);
                    if (!this.loyalty.rules_by_product_id[product.id]) {
                        this.loyalty.rules_by_product_id[product.id] = [rule];
                    } else if (rule.cumulative) {
                        this.loyalty.rules_by_product_id[product.id].unshift(rule);
                    } else {
                        this.loyalty.rules_by_product_id[product.id].push(rule);
                    }
                } else if ((rule.category_id instanceof Array) && rule.product_id == false) {
                    //var category = this.get_category_ancestors_ids(rule.category_id[0]);
                    //console.log('Category get by id', this.category_by_id);
                    if (!this.loyalty.rules_by_category_id[rule.category_id[0]]) {
                    this.loyalty.rules_by_category_id[rule.category_id[0]] = [rule];
                    } else if (rule.cumulative) {
                    this.loyalty.rules_by_category_id[rule.category_id[0]].unshift(rule);
                    } else {
                    this.loyalty.rules_by_category_id[rule.category_id[0]].push(rule);
                    }
                }
            }
        },
        add_rewards: function(rewards) {
           this.loyalty.rewards = rewards || {};
           this.loyalty.rewards_by_id = {};
           this.loyalty.product_by_reward_id = {};
           this.loyalty.reward_ancestors = {};
           this.loyalty.reward_all_product = {};
           for (var i = 0; i < rewards.length;i++) {
                var single_reward = rewards[i];
                var product;
                this.loyalty.rewards_by_id[single_reward.id] = single_reward;
                if (!this.loyalty.product_by_reward_id[single_reward.id]){
                    this.loyalty.product_by_reward_id[single_reward.id] = [];
                }
                if (!this.loyalty.reward_all_product['0']){
                    this.loyalty.reward_all_product['0'] = [];
                }
                if (single_reward.type === 'discount'){
                    this.loyalty.product_by_reward_id[single_reward.id].push(single_reward.discount_product_id[0]);
                    this.loyalty.reward_all_product['0'].push(single_reward.discount_product_id[0]);
                } else if (single_reward.type === 'gift'){
                    this.loyalty.product_by_reward_id[single_reward.id].push(single_reward.gift_product_id[0]);
                    this.loyalty.reward_all_product['0'].push(single_reward.gift_product_id[0]);
                } else if (single_reward.type === 'resale') {
                    this.loyalty.product_by_reward_id[single_reward.id].push(single_reward.point_product_id[0]);
                    this.loyalty.reward_all_product['0'].push(single_reward.point_product_id[0]);
                }
                this.loyalty.reward_ancestors[single_reward.id] = [single_reward.id];
           }
           this.loyalty.reward_all_product['0'] = this.loyalty.reward_all_product['0'].sort().filter(function(value, index, array) {
                                                return (index === 0) || (value !== array[index-1]);
                                                });
        },
        get_reward_by_id: function(id){
            if (id <= this.loyalty.rewards_by_id.light){
                return this.loyalty.rewards_by_id[id];
            } else {
                return [];
            }
        },
        get_product_by_reward: function(reward_id) {
            var product_ids  = this.loyalty.product_by_reward_id[reward_id];
            var list = [];
            if (product_ids) {
                for (var i = 0, len = Math.min(product_ids.length, this.limit); i < len; i++) {
                    list.push(this.product_by_id[product_ids[i]]);
                }
            }
            return list;
        },
        get_product_by_allreward: function() {
            var product_ids  = this.loyalty.reward_all_product['0'];
            var list = [];
            if (product_ids) {
                for (var i = 0, len = Math.min(product_ids.length, this.limit); i < len; i++) {
                    list.push(this.product_by_id[product_ids[i]]);
                }
            }
            return list;
        },
        get_reward_ancestors_ids: function(reward_id){
            return this.loyalty.reward_ancestors[reward_id] || [];
        },
    })

}
