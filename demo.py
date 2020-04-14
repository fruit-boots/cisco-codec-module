import ciscocodec
import pdb

def main():
    #attributes = {'device_name': 'BOS.Home.Adam.Bruneau', 'region': '', 'ip': '192.168.1.63', 'user': 'demo', 'password': 'BOSvcC1sco!', 'hw_version': '', 'sw_version': 'ce9.12.1.8a845789ad6', 'device_type': 'Cisco Webex DX80', 'sip': '', 'online': True, 'session_cookie': {'Cookie': 'SessionId=2dbbbaaa2423b90894db2bfba4a50d63dc74c058f5d0556d5e8035bfd7fad2b3'}, 'password_verified': True, 'macros_enabled': True, 'macros_autostart': True, 'number_of_macros': 2, 'has_zoom_button': True, 'number_of_panels': 0, 'number_of_extensions': 3, 'connected_devices': 0, 'serial_numbers': {'codec': 'FOC1833NB25'}, 'cdp': {'address': '', 'capabilities': '', 'deviceid': '', 'duplex': '', 'platform': '', 'portid': '', 'primarymgmtaddress': '', 'sysname': '', 'sysobjectid': '', 'vtpmgmtdomain': '', 'version': '', 'voipappliancevlanid': ''}}
    #codec = ciscocodec_v2.Codec('10.1.81.26', 'admin','BOSvcC1sco!','BOS.fenway')
    codec = ciscocodec.Codec('192.168.1.63', 'demo','BOSvcC1sco!','abruneau')

    codec.get_session_cookie()

    print(codec.session_cookie)

    codec.get_status_xml()
    codec.export_status(f'testing/codec_backups/{codec.device_name}')

    codec.get_configuration_xml()
    codec.export_configuration(f'testing/codec_backups/{codec.device_name}')

    codec.get_device_name()
    codec.get_macros_enabled()
    codec.get_macros_autostart()
    codec.get_macro_details()
    codec.export_macros(f"testing/codec_backups/{codec.device_name}")

    codec.get_extensions()
    codec.export_extensions(f"testing/codec_backups/{codec.device_name}")

    codec.get_connected_devices()
    codec.get_sip_uri()
    codec.get_sw_version()
    codec.get_device_type()
    codec.get_cdp()

    codec.enable_macros('off')
    codec.enable_macros('on')

    codec.upload_macro('upload_files/zoom_dial_v0.3.1.js','zoom_dial_v0_3_1')
    codec.upload_extension('upload_files/roomcontrolconfig.xml')
    print('\nuploaded\n')
    print(codec.extension_details)
    print(codec.macro_details)

    codec.delete_macro(codec.macro_details[0]['name'])
    codec.delete_all_extensions()
    print("\ndeleted\n")
    print(codec.extension_details)
    print(codec.macro_details)
    #codec.close_session()

if __name__ == '__main__':
    main()

