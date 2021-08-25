import ciscocodec
import pprint # Used to prettify the attributes to console

"""
You must obtain a cookie from the codec in order to use this module.
** Cookies are persistent until you close the session or reboot the codec. **

Available commands:

.check_online_status()
.get_cookie() - mandatory to use any methods below
.close_session() - always close if you are finished! You can also save this cookie to a file (pickle module works best).
.get() - see XMLAPI documentation from cisco
.post() - see XMLAPI documentation from cisco
.enable_macros() - on/off
.enable_autostart() - enables macros to start automatically
.set_ntp() - mode can be set to Auto, Manual, or Off.
    When setting the mode to manual, you must specify the addresses of the NTP servers.
    e.g. codec.set_ntp("Manual",addr1="192.168.1.1", addr2="192.168.50.1", addr3="192.168.100.1") 
.upload_macro()
.delete_macro()
.upload_extension()
.delete_extension()
.add_user()
.delete_user()
.get_codec_details() - retrieves the codecs attibutes mentioned below
.get_attributes() - returns a dictionary of the objects attributes
.set_attributes() - only recomended if you absoultely need it. This will override the objects attributes.
.set_ntp() - auto, manual, off. Manual requires ntp addresses in k,v format
.update_firmware() - requires url to where the .pkg file lives as a parameter

Object attributes (on instantiation):

        self.ip = ip
        self.user = user
        self.password = password
        
        # defaults
        self.online = False
        self.password_verified = None
        self.device_name = None
        self.device_type = None
        self.sw_version = None
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
        self.timeout = 10

"""

""" Gather codec information """
ip = input('Enter IP: ')
print('\nWhen entering user credentials ensure they are `Admin` level!')
user = input('Enter admin username: ')
password = input('Enter admin password: ')
codec = ciscocodec.Codec(ip, user, password)

# check online status
codec.check_online_status()

# get cookie to make calls
if codec.online:
    codec.get_cookie()

# make direct calls with get/post if you wish. Reference cisco XMLAPI documentation.
#codec.get('uri')
#codec.post('command')

# get codec information
if codec.session_cookie is not None:
    print('\nGetting codec information...\n')
    pprint.pprint(codec.get_codec_details())# make it readable

#-- Set some settings
#codec.enable_macros('off')
#codec.enable_macros('on')

#-- Upload/Delete some extensions and macros

#codec.upload_macro(file, macro_name)
#codec.upload_extension(file)
#print(codec.extension_details)
#print(codec.macro_details)

#-- Delete macros and extensions
# delete by name for macro, and by id for extensions

#codec.delete_macro('example')
#codec.delete_extension(codec.extension_details[0]['id'])

#print(codec.extension_details)
#print(codec.macro_details)

#-- Create/Delete user
#codec.create_user(username, password, role)
#codec.delete_user(username)

# close session
print('\nClosing session...\n')
print('Success closing session:',codec.close_session())
