Ext.define('MainHub.model.libraries.SampleNucleicAcidType', {
    extend: 'MainHub.model.Base',

    fields: [
        {
            type: 'int',
            name: 'id'
        },
        {
            type: 'string',
            name: 'name'
        },
        {
            type: 'string',
            name: 'type'
        },
        {
            type: 'bool',
            name: 'single_cell'
        }
    ]
});
