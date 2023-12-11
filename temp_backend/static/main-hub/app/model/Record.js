Ext.define('MainHub.model.Record', {
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
            name: 'record_type',
            type: 'string'
        },
        {
            name: 'status',
            type: 'int',
            allowNull: true
        },
        {
            name: 'barcode',
            type: 'string'
        },
        {
            name: 'is_converted',
            type: 'bool',
            defaultValue: false
        },
        {
            name: 'selected',
            type: 'bool',
            defaultValue: false
        }
    ],

    getRecordType: function() {
        var type = this.get('record_type');
        if (type === 'Sample' && this.get('is_converted')) {
            type = 'Library';
        }
        return type;
    },

    getBarcode: function() {
        var barcode = this.get('barcode');
        return this.get('is_converted') ? barcode + '*' : barcode;
    }
});
