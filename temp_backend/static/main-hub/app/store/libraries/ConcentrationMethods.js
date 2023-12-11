Ext.define('MainHub.store.libraries.ConcentrationMethods', {
    extend: 'Ext.data.Store',
    storeId: 'concentrationMethodsStore',

    requires: [
        'MainHub.model.libraries.ConcentrationMethod'
    ],

    model: 'MainHub.model.libraries.ConcentrationMethod',

    proxy: {
        type: 'ajax',
        url: 'api/concentration_methods/',
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
