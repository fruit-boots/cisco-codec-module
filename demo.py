import ciscocodec
import pdb

def main():
    #codec = ciscocodec.Codec('10.1.81.26', 'admin','BOSvcC1sco!','BOS.fenway')
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

