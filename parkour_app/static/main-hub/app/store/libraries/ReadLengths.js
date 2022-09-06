Ext.define('MainHub.store.libraries.ReadLengths', {
    extend: 'Ext.data.Store',
    storeId: 'readLengthsStore',

    requires: [
        'MainHub.model.libraries.ReadLength'
    ],

    model: 'MainHub.model.libraries.ReadLength',

    proxy: {
        type: 'ajax',
        url: 'api/read_lengths/',
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
