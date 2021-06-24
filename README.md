# cisco-codec-module
Utilizes XMLAPI to get/set certain attributes of a Cisco Codec.
Module will use Session Cookies. HTTP+HTTPS mode must be set on the codec for it to work.
Reference demo.py to see the module in action.

`ciscocodec.Codec(ip, user, password)` is need to instantiate the class.

Make sure to install the requirements shown in requirements.txt. This can be done by running `pip install -r requirements.txt`

See `demo.py` for an example.