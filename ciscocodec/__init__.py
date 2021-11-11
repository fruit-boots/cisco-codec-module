import socket

class Codec(object):

    from ._commands import get_codec_details
    from ._commands import upload_macro, delete_macro
    from ._commands import upload_extension, delete_extension
    from ._commands import add_user, delete_user
    from ._commands import enable_macros, enable_autostart
    from ._commands import set_ntp
    from ._commands import update_firmware
    from ._commands import presentation_selection
    from ._commands import get_diagnostics
    from ._xmlapi import get, post, get_cookie, close_session
    
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password
        
        # defaults
        self.online = False
        self.password_verified = None
        self.device_name = None
        self.device_type = None
        self.sw_version = None
        self.sip_uri = None
        self.users = None
        self.macro_capable = None
        self.macros_enabled = None
        self.macros_autostart = None
        self.macro_names = None
        self.macro_details = None
        self.number_of_panels = None
        self.number_of_extensions = None
        self.extension_details = None
        self.session_cookie = None
        self.configuration_xml = None
        self.status_xml = None
        self.diagnostics = None
        self.timeout = 10
        
    def get_attributes(self,detailed=False):      
        # copy it instead of directly changing it because it will alter the object attributes
        data = self.__dict__.copy()
        if detailed == False:
            [data.pop(key) for key in ['configuration_xml','status_xml','macro_details','extension_details','timeout']]
        return data

    def set_attributes(self, attributes):
        for k,v in attributes.items():
            setattr(self, k, v)

    def check_online_status(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect((self.ip, 443))
        except socket.timeout:
            self.online = False
        else:
            s.close()
            self.online = True
        return self.online

