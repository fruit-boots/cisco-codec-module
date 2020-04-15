import requests
import bs4
import json
import datetime
import logging
import time
import os
"""
Written by Adam Bruneau - bruneau.adam@bcg.com. Special thanks to Scott Thorton.

"""

class Codec:
    """ Interact with Cisco Codecs via XMLAPI. Instatiate class with a minimum dictionary containing ip, user, pass """
    def __init__(self, ip='xxx.xxx.xxx.xxx', user='admin', password='******', device_name='device_name'):
        self.ip = ip
        self.user = user
        self.password = password
        self.device_name = device_name

        # Set attribute flags to default
        self.region = None
        self.sw_version = None
        self.device_type = None
        self.sip = None
        self.online = False
        self.session_cookie = None
        self.http_secure = None
        self.password_verified = None
        self.macros_enabled = None
        self.macros_autostart = None
        self.number_of_macros = None
        self.macro_details = None
        self.has_zoom_button = None
        self.number_of_panels = None
        self.number_of_extensions = None
        self.status_xml = None
        self.configuration_xml = None
        self.connected_devices = None
        self.serial_numbers = None
        self.number_of_extensions = None
        self.extension_details = None
        self.cdp = None


    def get_attributes(self, all=False):
        """ Setting all = True will include XML, extension, and Macro details. """
        # show the codec attributes of the codec
        # copy it instead of directly changing it because it will alter the object attributes
        
        items = self.__dict__.copy()

        if not all:
            [items.pop(key) for key in ['status_xml','configuration_xml','macro_details','extension_details','http_secure']]
        return items
        
    def set_attributes(self, dictionary, overwrite=False, preserve_cookie=False):
        """ Setting overwrite to False will only populate keys that have a None value """
        # Update default attributes by the dictionary data if it matches the available attributes
        reference = self.get_attributes('all')
        
        for k,v in dictionary.items():
            if k in reference.keys() :
                if overwrite == True:
                    setattr(self, k, v)
                else:
                    if reference[k] == None:
                        setattr(self, k, v)
        if preserve_cookie == False:
            self.session_cookie = None
        return self.get_attributes('all')


    def get_session_cookie(self):
        """ Tries to get a session cookie. If HTTPS only, it will set the mode to HTTP/HTTPS """
        auth = requests.auth.HTTPBasicAuth(self.user, self.password)
        try:
            session = requests.post(f'http://{self.ip}/xmlapi/session/begin',auth=auth, verify=False)
        except requests.exceptions.ConnectionError as e:
            raise GeneralError(self, f"Cookie Request Failed.\n{e}")
        else:
            self.online = True
            # Set a flag for password, store the cookie
            if session.status_code == 204:
                self.password_verified = True
                try:
                    self.session_cookie = {'Cookie':'SessionId={}'.format(session.cookies['SessionId'])}
                except KeyError:
                    # try to set the http mode if https
                    if session.url.startswith('https'):
                        self.http_secure = True
                        self.set_http_mode()
                        for x in range(5):
                            # once the setting has changed, you need to wait for it to stick
                            time.sleep(3)
                            retry = requests.post(f'http://{self.ip}/xmlapi/session/begin',auth=auth, verify=False)
                            try:
                                self.session_cookie = {'Cookie':'SessionId={}'.format(retry.cookies['SessionId'])}
                            except KeyError:
                                continue
                            else:
                                self.http_secure = False
                                break
                else:
                    self.http_secure = False
                    return self.session_cookie
            if session.status_code == 200:
                self.password_verified = True
                self.session_cookie = None
                raise GeneralError(self, "HTTP request successful, but no cookie in response")
            if session.status_code == 401:
                self.password_verified = False
                self.session_cookie = None
                raise AuthenticationError(self, session)
            else:
                raise GeneralError(self, f"Cookie Request Failed.\n{session.content.decode()}")
      
    def close_session(self):
        """ Returns True if succesfull """
        if isinstance(self.session_cookie, dict):
            try:
                session = requests.post(f'http://{self.ip}/xmlapi/session/end', headers=self.session_cookie,verify=False)
            except requests.exceptions.ConnectionError as e:
                raise GeneralError(self, f"Issue when closing session for Cookie: {self.session_cookie['Cookie']}\n{e}")
            else:
                self.session_cookie = None
                if session.status_code == 204:
                    return True
                if session.status_code == 200:
                    return "Session cookie did not exist"
                else:
                    raise GeneralError(self, f"Something went wrong when closing the session.\n{session.content.decode()}")
        else:
            return

    def get_xml(self, query):
        """ Returns a request object when called directly. Use .content method to see the xml """
        if not isinstance(self.session_cookie, dict):
            raise GeneralError(self, "No session cookie available!")
        url = f'http://{self.ip}/{query}'      
        try:
            xml = requests.get(url, headers=self.session_cookie,verify=False)
        except requests.exceptions.ConnectionError as e:
            raise GeneralError(self, f"HTTP GET Request Failed!\n{e}")
        else:
            self.online = True
            # try getting another cookie if 401
            if xml.status_code == 401 and self.password_verified == True:
                print("Attempting to get another cookie")
                new_cookie = self.get_session_cookie()
                xml = requests.get(url, headers=new_cookie,verify=False)
                if xml.status_code == 401:
                    raise AuthenticationError(self)
                if xml.status_code == 200:
                    return xml
                if xml.status_code != 200:
                    raise GeneralError(self, xml.content.decode())
            # make sure XML is being returned
            if xml.content.decode().startswith('<?xml'):
                return xml
            # if not, get a new cookie
            else:
                print(f"Attempting to get another cookie for {self.device_name}")
                new_cookie = self.get_session_cookie()
                xml = requests.get(url, headers=new_cookie,verify=False)
                if xml.content.decode().startswith('<?xml'):
                    return xml
                else:
                    raise GeneralError(self, "Issue in getting XML response.")
            

    def put_xml(self, payload):
        """ Returns a request object when called directly. Use .content method to see the xml """
        if not isinstance(self.session_cookie, dict):
            raise GeneralError(self, "No session cookie avaiable!")
        # copy the cookie because we don't want to alter the stored one
        header=self.session_cookie.copy()
        header['Content-Type'] = 'text/xml'
        url = f'http://{self.ip}/putxml' 
        try:
            xml = requests.post(url, headers=header, data=payload, verify=False)
        except requests.exceptions.ConnectionError as e:
             raise GeneralError(self, f"HTTP POST Request Failed!\n{e}")
        else:
            self.online = True
            # try getting another cookie if 401
            if xml.status_code == 401 and self.password_verified == True:
                print("Attempting to get another cookie")
                # calling get_session_cookie() will store the new cookie in the object as well.
                new_cookie = self.get_session_cookie().copy() # Again, make a copy so to not alter the object attribute
                new_cookie['Content-Type'] = 'text/xml'
                xml = requests.post(url, headers=new_cookie, data=payload, verify=False)
                if xml.status_code == 401:
                    raise AuthenticationError(self)
                if xml.status_code == 200:
                    return xml
                if xml.status_code != 200:
                    raise GeneralError(self, xml.content.decode())
            if xml.content.decode().startswith('<?xml'):
                return xml
            else:
                print(f"Attempting to get another cookie for {self.device_name}")
                new_cookie = self.get_session_cookie().copy() # Again, make a copy so to not alter the object attribute
                new_cookie['Content-Type'] = 'text/xml'
                xml = requests.post(url, headers=new_cookie, data=payload, verify=False)
                if xml.content.decode().startswith('<?xml'):
                    return xml
                else:
                    raise GeneralError(self, "Issue in getting XML response.")

    def get_status_xml(self):
        """ Returns a request object when called directly. Use .content method to see the xml """
        r = self.get_xml('status.xml')
        if "</Status>" in r.content.decode():
            self.status_xml = r.content.decode()
        else:
            raise GeneralError(self, f"Status XML did not get returned\n{r.content.decode()}")
        return r

    def get_configuration_xml(self):
        """ Returns a request object when called directly. Use .content method to see the xml """
        r = self.get_xml('configuration.xml')
        if "</Configuration>" in r.content.decode():
            self.configuration_xml = r.content.decode()
        else:
            raise GeneralError(self, f"Configuration XML did not get returned correctly\n{r.content.decode()}")
        return r

    def set_http_mode(self, secure=False):
        """ Returns True if succesfull """
        if secure:
            mode = '<Configuration><NetworkServices><HTTP><Mode>HTTPS</Mode></HTTP></NetworkServices></Configuration>'
        else:
            mode= '<Configuration><NetworkServices><HTTP><Mode>HTTP+HTTPS</Mode></HTTP></NetworkServices></Configuration>'
        auth = requests.auth.HTTPBasicAuth(self.user, self.password)
        try:
            r = requests.post(f"https://{self.ip}/putxml", data=mode, auth=auth, verify=False)
        except requests.exceptions.ConnectionError as e:
            raise GeneralError(self, f"HTTP mode change failed!\n{e}")
        else:
            soup = bs4.BeautifulSoup(r.content.decode(), 'lxml')
            if "<Success/>" in r.content.decode():
                return True
            else:
                return
     
    # Below are some methods that will parse the status and config xml
    # This is much faster than trying to do XMLAPI calls for each item in question
    
    # --- Status.xml parsing starts here. --- #
    
    def get_device_name(self):
        """ Overwrites device name of object and returns it """
        if self.status_xml is None:
            raise GeneralError(self,"No status xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.status_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        else:
            try:
                name = soup.userinterface.find('name').text
            except AttributeError:
                return
            else:
                self.device_name = name
                return name
                
    def get_connected_devices(self):
        """ Updates total connected devices """
        if self.status_xml is None:
            raise GeneralError(self,"No status xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.status_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        else:
            devices = soup.find_all("connecteddevice")
            self.number_of_panels = 0
            self.connected_devices = 0
            for device in devices:
                try:
                    device = device.type.text
                except AttributeError:
                    # only way to skip
                    pass
                else:
                    self.connected_devices += 1
                    if device == "TouchPanel":
                        self.number_of_panels += 1
            return self.connected_devices
    
    def get_number_of_panels(self):
        """ Updates total connected Touch10's. """
        if self.status_xml is None:
            raise GeneralError(self,"No status xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.status_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        else:
            devices = soup.find_all("connecteddevice")
            self.number_of_panels = 0
            for device in devices:
                try:
                    device = device.type.text
                except AttributeError:
                    # only way to skip
                    pass
                else:
                    if device == "TouchPanel":
                        self.number_of_panels += 1
            return self.number_of_panels

    def get_serial_numbers(self):
        if self.status_xml is None:
            raise GeneralError(self,"No status xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.status_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        else:
            serials = dict()
            def _camera_serials(soup):
                try:
                    cams = soup.find_all('camera')
                except AttributeError:
                    return {}
                else:
                    # If it's a DX80 camera - skip
                    try:
                        cam = cams[0].model.text
                    except AttributeError:
                        pass
                    else:
                        if cam == 'DX80':
                            # return empty dictionary because we might not find serial numbers
                            return {}
                        else:
                            # dict comprehension with serial as key to avoid overwite accidents
                            return {cam.serialnumber.text:cam.model.text for cam in cams if cam.find('serialnumber') != None}
                            
            def _other_serials(soup):
                try:
                    devices = soup.find_all('connecteddevice')
                except AttributeError:
                    # return empty dictionary because we might not find serial numbers
                    return {}
                else:
                    # dict comprehension with serial as key to avoid overwite accidents
                    return {device.serialnumber.text:device.find('name').text for device in devices if device.find('serialnumber') != None}
            
            def _codec_serial(soup):
                try:
                    serial = soup.systemunit.hardware.module.serialnumber.text
                except AttributeError:
                    return
                else:
                    return serial
            
            # Readability prioritized here
            codec_serial = _codec_serial(soup)
            cams = _camera_serials(soup)
            others = _other_serials(soup)
            
            if cams != {}:
                serials['cameras'] = cams
                
            if others != {}:
                serials['other_devices'] = others
                
            if codec_serial != None:
                serials['codec'] = codec_serial
            
            if serials != {}:
                self.serial_numbers = serials
                return serials
            else:
                return
                
    def get_sip_uri(self):
        """ Returns string of SIP URI else None """
        if self.status_xml is None:
            raise GeneralError(self,"No status xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.status_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        else:
            try:
                uri = soup.find("sip").primary.uri.text
            except AttributeError:
                return
            else:
                self.sip = uri
                return self.sip
    
    def get_cdp(self):
        """ Returns dict of CDP info else None """
        if self.status_xml is None:
            raise GeneralError(self,"No status xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.status_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        else:
            try:
                cdp = soup.find("cdp")
            except AttributeError:
                return
            else:
                self.cdp = {tag.name:tag.text for tag in cdp.children if tag != '\n' and tag.text != None}                  
                return self.cdp

    def get_sw_version(self):
        if self.status_xml is None:
            raise GeneralError(self,"No status xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.status_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        try:
            sw = soup.find("systemunit").software.version.text
        except AttributeError:
           return
        else:
            self.sw_version = sw
            return self.sw_version
            
    def get_device_type(self):
        if self.status_xml is None:
            raise GeneralError(self,"No status xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.status_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        try:
            hw = soup.find("systemunit").productid.text
        except AttributeError:
           return
        else:
            self.device_type = hw
            return self.device_type
    
    # --- Configuration.xml parsing starts here. --- #
    
    def get_macros_enabled(self):
        if self.configuration_xml is None:
            raise GeneralError(self, "No configuration xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.configuration_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        try:
            macros = soup.find("macros").mode.text
        except AttributeError:
            return
        else:
            if macros == 'On':
                self.macros_enabled = True
            if macros == 'Off':
                self.macros_enabled = False
            return self.macros_enabled

    def get_macros_autostart(self):
        if self.configuration_xml is None:
            raise GeneralError(self, "No configuration xml to parse")
        try:
            soup = bs4.BeautifulSoup(self.configuration_xml, features='lxml')
        except Exception as e:
            raise GeneralError(self, e)
        try:
             macros_autostart = soup.find("macros").autostart.text
        except AttributeError:
            return
        else:
            if macros_autostart == 'On':
                self.macros_autostart = True
            if macros_autostart == 'Off':
                self.macros_autostart = False
            return self.macros_autostart

    def get_macro_details(self, zoom_macro_name='zoom_dial_v0_3_1'):
        # !! uses 'xml' parser vs 'lxml' !! #
        get_macros = self.put_xml('<Command><Macros><Macro><Get/></Macro></Macros></Command>')
        try:
            soup = bs4.BeautifulSoup(get_macros.content.decode(), features='xml')
        except Exception as e:
            raise GeneralError(self, e)
        else:
            macros = soup.find_all('Macro')
            if len(macros) > 0:
                try:
                    self.macro_details = [{'name':macro.find('Name').text, 'enabled': eval(macro.Active.text)} for macro in macros]
                except Exception as e:
                    raise GeneralError(self, e)
                else:
                    self.number_of_macros = len(self.macro_details)
                    for macro in self.macro_details:
                        macro_code = self.put_xml(f'<Command><Macros><Macro><Get><Name>{macro["name"]}</Name><Content>True</Content></Get></Macro></Macros></Command>')
                        try:
                            soup = bs4.BeautifulSoup(macro_code.content.decode(), features='xml')
                        except Exception as e:
                            raise GeneralError(self, e)
                        macro['code'] = soup.Content.text
                        if macro['name'] == zoom_macro_name:
                            self.has_zoom_button = True
                    return self.macro_details
            else:
                self.macro_details = None
                return
    
    def get_extensions(self):
        # !! uses 'xml' parser vs 'lxml' !! #
        ext = self.put_xml('<Command><UserInterface><Extensions><List/></Extensions></UserInterface></Command>')
        try:
            soup = bs4.BeautifulSoup(ext.content.decode(), features='xml')
        except Exception as e:
            raise GeneralError(self, e)
        else:
            exts = soup.find_all("Panel")
            if len(exts)> 0:
                try:
                    self.extension_details = [{'id':ext.find('PanelId').text, 'xml': str(ext)} for ext in exts]
                except Exception as e:
                    raise GeneralError(self, e)
                else:
                    self.number_of_extensions = len(self.extension_details)
                    return self.extension_details
            else:
                self.extension_details = None
                return
               
    def export_macros(self, folder):
        if self.macro_details is not None:
            if not os.path.exists(folder):
                os.makedirs(folder)
            for items in self.macro_details:
                with open(f'{folder}/{items["name"]}.js','w+') as output:
                    output.write(items['code'])
            return True
        else:
            return "No macro details available"
                
    def export_extensions(self, folder):
        if self.extension_details is not None:
            if not os.path.exists(folder):
                os.makedirs(folder)        
            xml_head = ""
            xml_footer = ""
            #xml_head = "<Extensions><Version>1.6</Version>\n"
            #xml_footer = "\n</Extensions>"
            for items in self.extension_details:
                with open(f'{folder}/{items["id"]}.xml','w+') as output:
                    xml = xml_head + items['xml'] + xml_footer
                    output.write(xml)
            return True
        else:
            return "No extension details available"
 
    def export_configuration(self, folder): 
        if self.configuration_xml is None:
            return "No configuration to export"
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(f"{folder}/configuration.xml", 'w+') as file:
            file.write(self.configuration_xml)
        return True
    
    def export_status(self, folder):
        if self.status_xml is None:
            return "No status xml to export"
        if not os.path.exists(folder):
            os.makedirs(folder)
        with open(f"{folder}/status.xml", 'w+') as file:
            file.write(self.status_xml)
        return True

    def upload_macro(self, filename, macro_name):
        """ Macro name can only contain "_" or "-" in macro name, no "." """
        if not os.path.exists(filename):
            raise GeneralError(self, f"No file exists! > {filename}")
        header = f'<?xml version="1.0"?><Command><Macros><Macro><Save><Name>{macro_name}</Name><Overwrite>False</Overwrite><body>'
        footer = f'</body></Save><Activate><Name>{macro_name}</Name></Activate></Macro><Runtime><Restart command=\'True\'></Restart></Runtime></Macros></Command>'
        with open(filename) as macro:
            p = self.put_xml(header + macro.read() + footer)
        soup = bs4.BeautifulSoup(p.content.decode(),'lxml')
        if all([soup.macrosaveresult.get('status') == 'OK', soup.macroactivateresult.get('status') == 'OK', soup.runtimerestartresult.get('status') == 'OK']):
            self.get_macro_details()
            return True
        else:
            try:
                err = soup.command.reason.text
            except AttributeError:
                raise GeneralError(self, p.content.decode())
            else:
                raise GeneralError(self, err)
                
    def upload_extension(self, filename):
        """ Takes an xml file exported from a codec and formats it correctly for upload """
        if not os.path.exists(filename):
            raise GeneralError(self, f"No file exists! > {filename}")
        with open(filename) as extension:
            raw = extension.read()
        soup = bs4.BeautifulSoup(raw, 'xml')
        panel = str(soup.PanelId) # <PanelId>panel_id</PanelId>
        raw = raw.replace(panel,'')
        raw = raw.replace('<','&lt;')
        raw = raw.replace('>','&gt;')
        header = f'<?xml version="1.0"?>\n<Command>\n<UserInterface>\n<Extensions>\n<Panel>\n<Save>\n{panel}\n<body>\n'
        footer = '</body>\n</Save>\n</Panel>\n</Extensions>\n</UserInterface>\n</Command>'
        payload = header + raw + footer
        p = self.put_xml(payload)
        soup = bs4.BeautifulSoup(p.content.decode(),'lxml')
        if soup.panelsaveresult.get('status') == 'OK':
            self.get_extensions()
            return True
        else:
            try:
                err = soup.command.reason.text
            except AttributeError:
                return
            else:
                return err        
            
    def enable_macros(self, mode='on'):
        if mode in ['on','off']:
            p = self.put_xml(f'<?xml version="1.0"?><Configuration><Macros><Mode>{mode}</Mode></Macros></Configuration>')
            if "Success" in p.content.decode():
                if mode == 'on':
                    self.macros_enabled = True
                else:
                    self.macros_enabled = False
                return True
            else:
                return
        else:
            raise GeneralError(self, "Mode must be either on or off")
            
    def delete_macro(self, name):
        p = self.put_xml(f'<?xml version="1.0"?><Command><Macros><Macro><Remove><Name>{name}</Name></Remove></Macro></Macros></Command>')
        soup = bs4.BeautifulSoup(p.content.decode(),'lxml')
        if soup.macroremoveresult.get('status') == 'OK':
            self.get_macro_details()
            return True
        else:
            try:
                err = soup.command.reason.text
            except AttributeError:
                return
            else:
                return err

    def delete_all_macros(self):
        p = self.put_xml(f'<?xml version="1.0"?><Command><Macros><Macro><RemoveAll/></Macro></Macros></Command>')
        soup = bs4.BeautifulSoup(p.content.decode(),'lxml')        
        if soup.macroremoveallresult.get('status') == 'OK':
            self.get_macro_details()
            return True
        else:
            try:
                err = soup.command.reason.text
            except AttributeError:
                return
            else:
                return err 
    
    def delete_extension(self, panelid):
        p = self.put_xml(f'<?xml version="1.0"?><Command><UserInterface><Extensions><Panel><Remove><PanelId>{panelid}</PanelId></Remove></Panel></Extensions></UserInterface></Command>')
        soup = bs4.BeautifulSoup(p.content.decode(),'lxml')        
        if soup.panelremoveresult.get('status') == 'OK':
            self.get_extensions()
            return True
        else:
            try:
                err = soup.command.reason.text
            except AttributeError:
                return
            else:
                return err    
    
    def delete_all_extensions(self):
        p = self.put_xml('<?xml version="1.0"?><Command><UserInterface><Extensions><Clear><ActivityType>Custom</ActivityType></Clear></Extensions></UserInterface></Command>')
        soup = bs4.BeautifulSoup(p.content.decode(),'lxml')        
        if soup.extensionsclearresult.get('status') == 'OK':
            time.sleep(1)
            self.get_extensions()
            return True
        else:
            try:
                err = soup.command.reason.text
            except AttributeError:
                return
            else:
                return err

#--- Error Handling ---#
# i know... it needs work

class AuthenticationError(Exception):
    """raises when an authentication error happens"""
    def __init__(self, codec, session):
        # limit the error to 200 chars
        msg = f"Authentication to {codec.device_name} ({codec.ip}) unsuccesful\nSTATUS: {session.status_code}\nBODY:\n{session.text}"
        logging.warning(msg)
        print(msg[:200])

class GeneralError(Exception):
    def __init__(self, codec, error):
        # limit the error to 200 chars
        msg = f"WARNING!\n\tCodec: {codec.device_name}\n\tIP: {codec.ip}\n\tIssue: {error}"
        logging.warning(msg)
        print(msg[:200])