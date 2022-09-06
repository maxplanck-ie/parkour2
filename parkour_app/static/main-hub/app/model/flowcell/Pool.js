Ext.define('MainHub.model.flowcell.Pool', {
    extend: 'MainHub.model.Base',

    fields: [
        {
            name: 'pk',
            type: 'int'
        },
        {
            name: 'name',
            type: 'string'
        },
        {
            name: 'read_length',
            type: 'int'
        },
        {
            name: 'read_length_name',
            type: 'string'
        },
        {
            name: 'pool_size',
            type: 'int'
        },
        {
            name: 'pool_size_id',
            type: 'int'
        },
        {
            name: 'loaded',
            type: 'int'
        },
        {
            name: 'ready',
            type: 'bool'
        }
    ],

    disabled: false,

    setDisabled: function(state) {
        this.disabled = state;
        this.store.fireEvent('disable', this, state);
    },

    isDisabled: function() {
        return this.disabled;
    }
});
