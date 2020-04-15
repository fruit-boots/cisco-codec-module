import ciscocodec

"""

Example of setiing up a codec from scratch. 

codec = ciscocodec.Codec(ip='192.168.1.63', user='demo',password='BOSvcC1sco!',device_name='abruneau')

Example of importing attributes to an object

codec = ciscocodec.Codec()
codec.set_attributes({'ip': '192.168.1.63', 'user': 'demo', 'password': 'BOSvcC1sco!', 'device_name': 'BOS.Home.Adam.Bruneau'}, overwrite=True, preserve_cookie=False)
# Overwrite will overwrite every single attribute.
# If overwrite is set to False, it will only overwrite attibutes that have a None value
# The preserve cookie flag set to False will set the cookie to None


"""

""" Gather codec information """
codec = ciscocodec.Codec(ip='192.168.1.63', user='demo',password='BOSvcC1sco!',device_name='abruneau')
codec.get_session_cookie()

codec.get_status_xml()
codec.get_configuration_xml()
# You must run the above in order to get any information
# If you import status_xml and coniguration_xml from .set_attributes() you will have old data!
codec.get_device_name()
codec.get_macros_enabled()
codec.get_macros_autostart()
codec.get_macro_details()
codec.get_extensions()
codec.get_connected_devices()
codec.get_sip_uri()
codec.get_sw_version()
codec.get_device_type()
codec.get_cdp()

""" Make some backups """
codec.export_status(f'testing/codec_backups/{codec.device_name}')
codec.export_configuration(f'testing/codec_backups/{codec.device_name}')
codec.export_extensions(f"testing/codec_backups/{codec.device_name}")
codec.export_macros(f"testing/codec_backups/{codec.device_name}")


""" Set some settings """
codec.enable_macros('off')
codec.enable_macros('on')

""" Upload some extensions and macros """
codec.upload_macro('upload_files/zoom_dial_v0.3.1.js','zoom_dial_v0_3_1')
codec.upload_extension('upload_files/roomcontrolconfig.xml')
print('\nuploaded\n')
print(codec.extension_details)
print(codec.macro_details)

""" Delete macros and extensions """
# delete by name for macro, and by id for extensions
codec.delete_macro(codec.macro_details[0]['name'])
# OR codec.delete_all_macros()
codec.delete_extension(codec.extension_details[0]['id'])
# OR codec.delete_all_extensions()
print("\ndeleted first entry in macros and extensions\n")
print(codec.extension_details)
print(codec.macro_details)

# !! Make sure to close session !! #

