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

function pos_loyalty_bg_screens(instance, module){ //module is instance.point_of_sale
    var QWeb = instance.web.qweb,
    _t = instance.web._t;

    var round_pr = instance.web.round_precision

    module.RewardProductScreenWidget = module.ScreenWidget.extend({
        template:'ProductScreenWidget',

        start: function(options){ //FIXME this should work as renderElement... but then the categories aren't properly set. explore why
            var self = this;
            console.log("Screen this", this);
            console.log("Screen self", self);
            console.log("Screen options", options);
            this.product_list_widget = new module.ProductListWidget(this,{
                click_product_action: function(product){
                    if(product.to_weight && self.pos.config.iface_electronic_scale){
                        self.pos_widget.screen_selector.set_current_screen('scale',{product: product});
                    }else{
                        var reward = rewards[this.product_categories_widget.dataset['rewardId']];
                        if (reward.type === 'gift'){
                            reward.gift_product_id = product.id;
                        } else if (reward.type === 'discount'){
                            reward.discount_product_id = product.id;
                        } else if (reward.type === 'resale'){
                            reward.point_product_id = product.id;
                        }
                        self.pos.get_order().apply_reward(reward);
                    }
                },
                product_list: this.product_list,
            });
            console.log("replace", this.product_list_widget);
            this.product_list_widget.replace(this.$('.placeholder-ProductListWidget'));
            console.log("replace", this.product_list_widget);
            this.product_categories_widget = new module.RewardCategoriesWidget(this,{
                product_list_widget: this.product_list_widget,
            });
            console.log("replace", this.product_categories_widget);
            this.product_categories_widget.replace(this.$('.placeholder-ProductCategoriesWidget'));
        },

        show: function(){
            this._super();
            var self = this;

            this.product_categories_widget.reset_reward();

            //this.pos_widget.order_widget.set_editable(true);
        },

        close: function(){
            this._super();
            //this.pos_widget.order_widget.set_editable(false);
        },
    });
}
