Ext.define('validator.Unique', {
    extend: 'Ext.data.validator.Validator',
    alias: 'data.validator.unique',
    validate: function(value, record) {
        var dataIndex = this.dataIndex;
        var store = record.store;
        var values = [];

        store.each(function(item) {
            var currentValue = item.get(dataIndex);
            if (item !== record && currentValue !== '') {
                values.push(currentValue);
            }
        });

        return values.indexOf(value) === -1 || 'Must be unique';
    }
});

Ext.define('validator.GreaterThanZero', {
    extend: 'Ext.data.validator.Validator',
    alias: 'data.validator.greaterthanzero',
    validate: function(value) {
        return (value > 0) || 'Must be greater than zero';
    }
});

Ext.define('MainHub.model.libraries.BatchAdd.Common', {
    extend: 'Ext.data.Model',

    fields: [
        {
            type: 'string',
            name: 'name'
        },
        {
            type: 'int',
            name: 'library_protocol',
            allowNull: true,
            defaultValue: null
        },
        {
            type: 'int',
            name: 'library_type',
            allowNull: true,
            defaultValue: null
        },
        {
            type: 'float',
            name: 'sequencing_depth',
            defaultValue: null
        },
        {
            type: 'float',
            name: 'concentration',
            defaultValue: null
        },
        {
            type: 'int',
            name: 'concentration_method',
            allowNull: true,
            defaultValue: null
        },
        {
            type: 'int',
            name: 'amplification_cycles',
            defaultValue: null
        },
        {
            type: 'bool',
            name: 'equal_representation_nucleotides'
        },
        {
            type: 'int',
            name: 'read_length',
            allowNull: true,
            defaultValue: null
        },
        {
            type: 'int',
            name: 'organism',
            allowNull: true,
            defaultValue: null
        },
        {
            type: 'string',
            name: 'comments'
        },
        {
            type: 'bool',
            name: 'invalid',
            defaultValue: false
        },
        {
            type: 'auto',
            name: 'errors',
            defaultValue: {}
        }
    ],

    validators: {
        name: [{
            type: 'presence'
        },{
            type: 'unique',
            dataIndex: 'name'
        }],
        library_protocol: 'presence',
        library_type: 'presence',
        concentration: 'presence',
        read_length: 'presence',
        sequencing_depth: 'greaterthanzero',
        amplification_cycles: 'presence',
        concentration_method: 'presence',
        organism: 'presence'
    }
});
