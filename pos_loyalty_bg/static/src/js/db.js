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
           for (var i = 0; i < rewards.length;i++) {
                this.loyalty.rewards_by_id[rewards[i].id] = rewards[i];
           }
        },
    })

}
