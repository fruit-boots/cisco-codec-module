# cisco-codec-module
Utilizes XMLAPI to get/set certain attributes of a Cisco Codec.
Module will use Session Cookies. HTTP+HTTPS mode must be set on the codec for it to work.
Reference demo.py to see the module in action.

`ciscocodec(ip, user, password)` is need to instantiate the class.

After instantiation you can import attributes by using `.set_attributes()` method. This will take a dictionary and set the attributes accordingly.

See `demo.py` for an example.