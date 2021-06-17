import socket

class Codec(object):

    from ._commands import get_config, get_status
    from ._commands import upload_macro, delete_macro
    from ._commands import upload_extension, delete_extension
    from ._commands import create_user, delete_user
    from ._commands import enable_macros, enable_autostart
    from ._xmlapi import get, post, get_cookie, close_session
    
    def __init__(self, ip, user, password):
        self.ip = ip
        self.user = user
        self.password = password

        # defaults
        self.configuration_xml = None
        self.timeout = 10
        self.session_cookie = None
        self.sw_version = None
        self.device_type = None
        self.online = False
        self.password_verified = None
        self.macros_enabled = None
        self.macros_autostart = None
        self.macro_names = None
        self.macro_details = None
        self.number_of_panels = None
        self.number_of_extensions = None
        self.status_xml = None
        self.number_of_extensions = None
        self.extension_details = None
        
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
            s.connect((self.ip, 80))
        except socket.timeout:
            self.online = False
        else:
            s.close()
            self.online = True
        return self.online
