Ext.define('MainHub.view.requests.EmailWindowController', {
    extend: 'Ext.app.ViewController',
    alias: 'controller.requests-emailwindow',
    requires: [],

    config: {
        control: {
            '#': {
                boxready: 'boxready'
            },
            '#send-email-button': {
                click: 'send'
            }
        }
    },

    boxready: function(wnd) {
        var subjectField = wnd.down('#subject-field');
        subjectField.setValue(wnd.record.get('name'));
    },

    send: function(btn) {
        var wnd = btn.up('window');
        var form = wnd.down('#email-form').getForm();

        if (!form.isValid()) {
            new Noty({ text: 'All fields must be filled in.', type: 'warning' }).show();
            return;
        }

        form.submit({
            url: Ext.String.format('api/requests/{0}/send_email/', wnd.record.get('pk')),
            params: form.getFieldValues(),
            success: function(f, action) {
                new Noty({ text: 'Email has been sent!' }).show();
                wnd.close();
            },
            failure: function(f, action) {
                var error = action.result ? action.result.error : action.response.statusText;
                new Noty({ text: error, type: 'error' }).show();
                console.error(action);
            }
        });
    }
});
