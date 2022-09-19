Ext.define('MainHub.model.libraries.Index', {
    extend: 'MainHub.model.Base',

    fields: [
        {
            name: 'id',
            type: 'int'
        },
        {
            name: 'name',
            type: 'string'
        },
        {
            name: 'index',
            type: 'string'
        },
        {
            name: 'index_id',
            type: 'string'
        }
    ]
});
