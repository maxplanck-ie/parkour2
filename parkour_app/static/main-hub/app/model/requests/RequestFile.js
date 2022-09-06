Ext.define('MainHub.model.requests.RequestFile', {
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
            name: 'size',
            type: 'string'
        },
        {
            name: 'path',
            type: 'string'
        }
    ]
});
