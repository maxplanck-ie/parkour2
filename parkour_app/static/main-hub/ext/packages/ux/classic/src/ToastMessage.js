/**
 *   Ext.toast Wrapper
 *
 *   Example usage:
 *
 *   Ext.ux.ToastMessage('Message', 'error', 'My Title', false, 'br')
 *
 *   or
 *
 *   Ext.ux.ToastMessage({
 *      html: 'Message',
 *      msgType: 'error',
 *      title: 'My Title',
 *      autoClose: false,
 *      align: 'br'
 *   });
 */

Ext.define('Ext.ux.ToastMessage', {
    alias: 'widget.toast_msg',
    title: '',
    html: '',
    autoClose: true,
    autoCloseDelay: 10000,
    align: 'br',

    defaultTypes: {
        error: 'Error',
        warning: 'Warning',
        default: 'Information'
    },

    colors: {
        error: '#ff6c80',
        warning: '#d7bf0c'
    },

    constructor: function (config) {
        this.msgType = (config.msgType) ? config.msgType : 'default';

        Ext.applyIf(config, {
            msgType: 'default',
            autoClose: this.autoClose,
            autoCloseDelay: this.autoCloseDelay,
            // minWidth: 125,
            // maxWidth: 300,
            width: 250,
            minHeight: 150,
            // height: 'auto',
            align: this.align
        });

        config.title = this._get_title(config.title);
        config.html = this._get_msg_body(config.html);

        this.config = config;

        Ext.toast(this.config);

        this.callParent(arguments);
    },

    _get_title: function (title) {
        // if (title) {
        //     title = this._get_styled_text(title, this.msgType);
        // } else {
        //     var defaultTitle = this.defaultTypes[this.msgType];
        //     title = this._get_styled_text((defaultTitle) ? defaultTitle : this.defaultTypes['default'], this.msgType);
        // }

        if (!title) {
            title = this.defaultTypes[this.msgType];
        }

        return title;
    },

    _get_msg_body: function (msg) {
        return this._get_styled_text(msg);
    },

    _get_styled_text: function (msg) {
        var color = this.colors[this.msgType];

        if (color) {
            msg = '<div style="color: ' + color + ';"><strong>' + msg + '</strong></div>';
        }

        return msg;
    }
},

function (ToastMessage) {
    Ext.ux.ToastMessage = function (msg, msgType, title, autoClose, align) {
        var config = {};

        if (Ext.isObject(msg)) {
            config = msg;
        } else {
            config = {
                title: title,
                html: msg,
                msgType: msgType,
                autoClose: autoClose,
                align: align
            };
        }

        return new ToastMessage(config);
    }
});
