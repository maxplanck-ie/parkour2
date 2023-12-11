Ext.define('MainHub.store.libraries.NucleicAcidTypes', {
    extend: 'Ext.data.Store',
    storeId: 'nucleicAcidTypesStore',

    requires: [
        'MainHub.model.libraries.SampleNucleicAcidType'
    ],

    model: 'MainHub.model.libraries.SampleNucleicAcidType',

    proxy: {
        type: 'ajax',
        url: 'api/nucleic_acid_types/',
        timeout: 1000000,
        pageParam: false,   //to remove param "page"
        startParam: false,  //to remove param "start"
        limitParam: false,  //to remove param "limit"
        noCache: false,     //to remove param "_dc",
        reader: {
            type: 'json',
            rootProperty: 'data',
            successProperty: 'success'
        }
    },

    autoLoad: true
});
