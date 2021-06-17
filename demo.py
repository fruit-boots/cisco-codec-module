from ciscocodec import Codec

"""

Example of setiing up a codec from scratch. 

codec = ciscocodec.Codec(ip='192.168.1.63', user='demo',password='BOSvcC1sco!',device_name='abruneau')

Example of importing attributes to an object
codec.set_attributes({'ip': '192.168.1.63', 'user': 'demo', 'password': 'BOSvcC1sco!', 'device_name': 'BOS.Home.Adam.Bruneau'})

"""

""" Gather codec information """
ip = input('Enter IP: ')
user = input('Enter admin username: ')
password = input('Enter admin password')

codec = ciscocodec.Codec(ip, user, password)
# get cookie to make calls
codec.get_cookie()

# make direct calls with get/post
#codec.get(information)
#codec.post(command)

# get codec information
codec.get_config()
codec.get_status()

#-- Set some settings
#codec.enable_macros('off')
#codec.enable_macros('on')

#-- Upload/Delete some extensions and macros
'''
codec.upload_macro(file, name)
codec.upload_extension(file)
print(codec.extension_details)
print(codec.macro_details)

#-- Delete macros and extensions
# delete by name for macro, and by id for extensions
codec.delete_macro('example'))
codec.delete_extension(codec.extension_details[0]['id'])

print(codec.extension_details)
print(codec.macro_details)
'''

#-- Create/Delete user
'''
codec.create_user(username, password, role)
codec.delete_user(username)
'''

# close session
codec.close_session()
