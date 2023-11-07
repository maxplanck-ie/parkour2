Ext.define('MainHub.model.libraries.LibraryProtocol', {
    extend: 'MainHub.model.Base',

    fields: [{
        type: 'int',
        name: 'id'
    },
    {
        type: 'string',
        name: 'name'
    },
    {
        type: 'string',
        name: 'provider'
    },
    {
        type: 'string',
        name: 'catalog'
    },
    {
        type: 'string',
        name: 'explanation'
    },
    {
        type: 'string',
        name: 'input_requirements'
    },
    {
        type: 'string',
        name: 'typical_application'
    },
    {
        type: 'string',
        name: 'comments'
    }
    ]
});
