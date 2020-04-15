# cisco-codec-module
Utilizes XMLAPI to get/set certain attributes of a Cisco Codec.
Module will use Session Cookies. HTTP+HTTPS mode must be set on the codec for it to work.
Reference demo.py to see the module in action.

`Codec(ip, user, password)` is need to instantiate the class.

After instantiation you can import attributes by using `.set_attributes()` method. This will take a dictionary and set the attributes accordingly. If the overwrite flag is set to True, all attributes will be overwritten. Otherwise, only attributes with None values will be overwritten. To see the availble attributes run `.get_attributes(all=True)`
