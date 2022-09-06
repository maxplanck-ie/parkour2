Ext.define('MainHub.model.flowcell.Lane', {
    extend: 'MainHub.model.Base',

    fields: [{
        name: 'pool_id',
        type: 'int'
    }, {
        name: 'pool_name',
        type: 'string'
    }, {
        name: 'lane_id',
        type: 'string'
    }, {
        name: 'lane_name',
        type: 'string'
    }, {
        name: 'loaded',
        type: 'int'
    }]
});
