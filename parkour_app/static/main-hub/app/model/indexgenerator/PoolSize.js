Ext.define('MainHub.model.indexgenerator.PoolSize', {
    extend: 'MainHub.model.Base',

    fields: [{
        name: 'id',
        type: 'int'
    }, {
        name: 'name',
        type: 'string'
    }, {
        name: 'multiplier',
        type: 'int'
    }, {
        name: 'size',
        type: 'int'
    }]
});
