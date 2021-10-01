import bs4
import os
import requests.exceptions.ReadTimeout from requests

def get_codec_details(self):
    # status xml parsing
    self.status_xml = self.get('status.xml')
    _get_device_name(self)
    _get_number_of_panels(self)
    _get_sw_version(self)
    _get_device_type(self)
    _get_macro_capable(self)
    _get_sip_uri(self)
    # config xml parsing
    self.configuration_xml = self.get('configuration.xml')
    if self.macro_capable:
        _get_macros_enabled(self)
        _get_macros_autostart(self)
        _get_macro_details(self)
    _get_extensions(self)
    # user details
    _get_users(self)
    return self.get_attributes()

# -- Upload/Delete Macros and Extensions -- #

def upload_macro(self, filename, macro_name):
    if self.macro_capable is None:
        raise Exception("Unable to know if codec supports macros. Run `.update_codec_details()`")    
    elif not self.macro_capable:
        raise Exception("Device is unable to use macros")
    # Macro name can only contain "_" or "-" in macro name, no "."
    if not os.path.exists(filename):
        raise Exception(f"No file exists! > {filename}")
    if " " in macro_name or "." in macro_name:
        raise Exception("Cannot export a macro with illegal characters (spaces or periods)")
    header = f'<?xml version="1.0"?><Command><Macros><Macro><Save><Name>{macro_name}</Name><Overwrite>False</Overwrite><body>'
    footer = f'</body></Save><Activate><Name>{macro_name}</Name></Activate></Macro><Runtime><Restart command=\'True\'></Restart></Runtime></Macros></Command>'
    with open(filename) as macro:
        payload = macro.read().replace('<','&lt;').replace('>','&gt;').replace('"',"&quot;").replace('&&','&amp;&amp;')
        p = self.post(header + payload + footer)
    try:
        soup = bs4.BeautifulSoup(p,'lxml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
    if all([soup.macrosaveresult.get('status') == 'OK', soup.macroactivateresult.get('status') == 'OK', soup.runtimerestartresult.get('status') == 'OK']):
        _get_macro_details(self)
        return True
    else:
        try:
            err = soup.command.reason.text
        except AttributeError:
            raise Exception(f'Error not found -> {err}')
        else:
            raise Exception(f'Error from {self.ip} -> {err}')

def delete_macro(self, name):
    if not self.macro_capable:
        raise Exception("Device is unable to use macros")
    p = self.post(f'<?xml version="1.0"?><Command><Macros><Macro><Remove><Name>{name}</Name></Remove></Macro></Macros></Command>')
    soup = bs4.BeautifulSoup(p,'lxml')
    if soup.macroremoveresult.get('status') == 'OK':
        _get_macro_details(self)
        return True
    else:
        try:
            err = soup.command.reason.text
        except AttributeError:
            raise Exception(f'Error not found -> {err}')
        else:
            raise Exception(f'Error from {self.ip} -> {err}')

def upload_extension(self, filename):
    """ Takes an xml file exported from a codec and formats it correctly for upload """
    if not os.path.exists(filename):
        raise Exception(f"No file exists! > {filename}")
    with open(filename) as extension:
        raw = extension.read()
    soup = bs4.BeautifulSoup(raw, 'xml')
    panel = str(soup.PanelId) # <PanelId>panel_id</PanelId>
    raw = raw.replace(panel,'')
    header = f'<?xml version="1.0"?>\n<Command>\n<UserInterface>\n<Extensions>\n<Panel>\n<Save>\n{panel}\n<body>\n'
    footer = '</body>\n</Save>\n</Panel>\n</Extensions>\n</UserInterface>\n</Command>'
    payload = header + raw + footer
    p = self.post(payload)
    try:
        soup = bs4.BeautifulSoup(p,'lxml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
    if soup.panelsaveresult.get('status') == 'OK':
        _get_extensions(self)
        return True
    else:
        try:
            err = soup.command.reason.text
        except AttributeError:
            raise Exception(f'Error not found -> {err}')
        else:
            raise Exception(f'Error from {self.ip} -> {err}')

def delete_extension(self, panelid):
    p = self.post(f'<?xml version="1.0"?><Command><UserInterface><Extensions><Panel><Remove><PanelId>{panelid}</PanelId></Remove></Panel></Extensions></UserInterface></Command>')
    soup = bs4.BeautifulSoup(p,'lxml')        
    if soup.panelremoveresult.get('status') == 'OK':
        _get_extensions(self)
        return True
    else:
        try:
            err = soup.command.reason.text
        except AttributeError:
            raise Exception(f'Error not found -> {err}')
        else:
            raise Exception(f'Error from {self.ip} -> {err}')

# -- User Commands -- #

def add_user(self, username, password, role):
    """ Roles : Admin/Audit/Integrator/RoomControl/User """
    payload = f'''<Command><UserManagement><User><Add>
    <Active>True</Active>
    <PassphraseChangeRequired>False</PassphraseChangeRequired>
    <Passphrase>{password}</Passphrase>
    <Role>{role}</Role>
    <YourPassphrase>{self.password}</YourPassphrase>
    <Username>{username}</Username>
    </Add></User></UserManagement></Command>'''
    p = self.post(payload)
    try:
        soup = bs4.BeautifulSoup(p,'lxml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
    if soup.useraddresult.get('status') == 'OK':
        _get_users(self)
        return True
    else:
        try:
            err = soup.command.reason.text
        except AttributeError:
            raise Exception(f'Error not found -> {err}')
        else:
            if "User already exists" in err:
                _get_users(self)
                return err
            else:
                raise Exception(f'Error from {self.ip} -> {err}')

def delete_user(self, username):
    payload = f'''<Command><UserManagement><User><Delete>
    <YourPassphrase>{self.password}</YourPassphrase>
    <Username>{username}</Username>
    </Delete></User></UserManagement></Command>'''
    p = self.post(payload)
    try:
        soup = bs4.BeautifulSoup(p,'lxml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
    if soup.userdeleteresult.get('status') == 'OK':
        _get_users(self)
        return True
    else:
        try:
            err = soup.command.reason.text
        except AttributeError:
            raise Exception(f'Error not found -> {err}')
        else:
            if f"User '{username}' does not exist" in err:
                _get_users(self)
                return err
            else:
                raise Exception(f'Error from {self.ip} -> {err}')

# -- Macro Setting Commands -- #

def enable_macros(self, mode='on'):
    if not self.macro_capable:
        return "Device is unable to use macros"
    elif self.macro_capable is None:
        raise Exception("Unable to know if codec supports macros. Run `.update_codec_details()`")
    if mode in ['on','off']:
        p = self.post(f'<?xml version="1.0"?><Configuration><Macros><Mode>{mode}</Mode></Macros></Configuration>')
        if "Success" in p:
            if mode == 'on':
                self.macros_enabled = True
            else:
                self.macros_enabled = False
            return True
        else:
            raise Exception(f"Macro setting did not succeed -> {p}")
    else:
        raise Exception("Mode must be either `on` or `off`")

def enable_autostart(self, mode='on'):
    if not self.macro_capable:
        return "Device is unable to use macros"
    elif self.macro_capable is None:
        raise Exception("Unable to know if codec supports macros. Run `.update_codec_details()`")
    if mode in ['on','off']:
        p = self.post(f'<?xml version="1.0"?><Configuration><Macros><Autostart>{mode}</Autostart></Macros></Configuration>')
        if "Success" in p:
            if mode == 'on':
                self.macros_enabled = True
            else:
                self.macros_enabled = False
            return True
        else:
            raise Exception(f"Macro setting did not succeed -> {p}")
    else:
        raise Exception("Mode must be either `on` or `off`")

# -- NTP Settings -- #

def set_ntp(self, mode, **addresses):
    if mode not in ['Auto','Manual','Off']:
        raise Exception("Mode must be 'Auto','Manual', or 'Off'")
    else:
        header = f"""<Configuration>
        <NetworkServices>
        <NTP>
        <Mode valueSpaceRef="/Valuespace/TTPAR_AutoManualOff">{mode}</Mode>
        """
        body = ""
        footer = """
        </NTP>
        </NetworkServices>
        </Configuration>"""
    if mode == 'Manual':
        if len(addresses.values()) == 0:
            raise Exception("Manual NTP requires addresses!")
        else:
            pos = 0
            for addr in addresses.values():
                pos +=1
                body += f"""<Server item="{pos}" maxOccurrence="3">
                <Address valueSpaceRef="/Valuespace/STR_0_255_NoFilt">{addr}</Address>
                <Key valueSpaceRef="/Valuespace/PASSWORD_0_2045_NoFilt">***</Key>
                <KeyAlgorithm valueSpaceRef="/Valuespace/TTPAR_NtpKeyAlgorithm">SHA256</KeyAlgorithm>
                <KeyId valueSpaceRef="/Valuespace/STR_0_10_NoFilt"></KeyId>
                </Server>
                """
    payload = header + body + footer
    p = self.post(payload)
    if "<Success/>" in p:
        return True
    else:
        try:
            soup = bs4.BeautifulSoup(p,'lxml')
        except Exception as e:
            raise Exception(f'Issue parsing XML -> {e}')
        else:
            try:
                err = soup.command.reason.text
            except AttributeError:
                raise Exception(f'Error not found -> {err}')
            else:
                raise Exception(f'Error from {self.ip} -> {err}')

# -- Firmware update -- #

def update_firmware(self, url):
    payload = f"""<Command>
    <SystemUnit>
    <SoftwareUpgrade>
    <URL>{url}</URL>
    </SoftwareUpgrade>
    </SystemUnit>
    </Command>"""
    try:
        p = self.post(payload)
    except requests.exceptions.ReadTimeout:
        return "Beginning update..."
    
def presentation_selection(self, source, mode):
    """ Modes available: "AutoShare", "Desktop", "Manual", "OnConnect" """
    if mode not in ["AutoShare","Desktop","Manual","OnConnect"]:
        raise Exception('Mode must be either "AutoShare", "Desktop", "Manual", or "OnConnect"')
    p = self.post(f'<?xml version="1.0"?><Configuration><Video><Input><Connector item="{source}"><PresentationSelection>{mode}</PresentationSelection></Connector></Input></Video></Configuration>')        
    if "<Success/>" in p:
        return True
    else:
        try:
            soup = bs4.BeautifulSoup(p,'lxml')
            err = soup.command.reason.text
        except AttributeError:
            raise Exception(f'Error not found -> {err}')
        else:
            raise Exception(f'Error from {self.ip} -> {err}')
    

# ---- PRIVATE METHODS ---- #

def _get_users(obj):
    users = []
    payload = '<Command><UserManagement><User><List></List></User></UserManagement></Command>'
    p = obj.post(payload)
    try:
        soup = bs4.BeautifulSoup(p,'lxml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
    if soup.userlistresult.get('status') == 'OK':
        all_users = soup.find_all('user')
        for user in all_users:
            roles = []
            for role in user.find_all('roles'):
                roles.append(role.text.replace('\n',''))
            users.append({'username':user.username.text,'roles':roles,'active':eval(soup.active.text)})
        obj.users = users
    else:
        try:
            err = soup.command.reason.text
        except AttributeError:
            raise Exception(f'Error not found -> {err}')
        else:
            raise Exception(f'Error from {self.ip} -> {err}')

# -- configuration XML parsing -- #

# -- Macro Parsing -- #

def _get_macros_enabled(obj):
    try:
        soup = bs4.BeautifulSoup(obj.configuration_xml, features='lxml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
    try:
        macros = soup.find("macros").mode.text
    except AttributeError:
        raise Exception("Could not find macros enabled in config xml")
    else:
        if macros == 'On':
            obj.macros_enabled = True
        if macros == 'Off':
            obj.macros_enabled = False

def _get_macros_autostart(obj):
    try:
        soup = bs4.BeautifulSoup(obj.configuration_xml, features='lxml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
    try:
         macros_autostart = soup.find("macros").autostart.text
    except AttributeError:
        raise Exception("Could not find macros autostart attribute in config xml")
    else:
        if macros_autostart == 'On':
            obj.macros_autostart = True
        if macros_autostart == 'Off':
            obj.macros_autostart = False

def _get_macro_details(obj):
    # !! uses 'xml' parser vs 'lxml' !! #
    get_macros = obj.post('<Command><Macros><Macro><Get/></Macro></Macros></Command>')
    try:
        soup = bs4.BeautifulSoup(get_macros, features='xml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
    else:
        macros = soup.find_all('Macro')
        if len(macros) > 0:
            try:
                obj.macro_details = [{'name':macro.find('Name').text, 'enabled': eval(macro.Active.text)} for macro in macros]
            except Exception as e:
                raise Exception(f'Issue parsing XML for macro details -> {e}')
            else:
                obj.macro_names = [mac['name'] for mac in obj.macro_details]
                for macro in obj.macro_details:
                    macro_code = obj.post(f'<Command><Macros><Macro><Get><Name>{macro["name"]}</Name><Content>True</Content></Get></Macro></Macros></Command>')
                    try:
                        soup = bs4.BeautifulSoup(macro_code, features='xml')
                    except Exception as e:
                        raise Exception(f'Issue parsing XML for macro {macro["name"]}-> {e}')
                    else:
                        macro['code'] = soup.Content.text
        else:
            obj.macro_details = None
            obj.macro_names = None

# -- Extension parsing -- #

def _get_extensions(obj):
    """ Returns a list containing dicts with keys "panel_id" and "xml" """
    # !! uses 'xml' parser vs 'lxml' !! #
    ext = obj.post('<Command><UserInterface><Extensions><List/></Extensions></UserInterface></Command>')
    try:
        soup = bs4.BeautifulSoup(ext, features='xml')
    except Exception as e:
        raise Exception(f'Issue parsing XML for Extension details -> {e}')
    else:
        exts = soup.find_all("Panel")
        if len(exts)> 0:
            version = soup.find("Version").text
            header = f'<Extensions><Version>{version}</Version>\n'
            footer = '</Extensions>'
            # xml return does not format the text chars for upload properly.
            # See encode/decode line in list comprehension.
            obj.extension_details = [{"panel_id":ext.find("PanelId").text,"xml":header+str(ext).encode("ascii", "xmlcharrefreplace").decode()+footer} for ext in exts]
            obj.number_of_extensions = len(obj.extension_details)
        else:
            obj.extension_details = None

# -- Status XML parsing -- #

def _get_device_name(obj):
    try:
        soup = bs4.BeautifulSoup(obj.status_xml, features='lxml')
    except Exception as e:
        raise Exception(f"Issue trying to parse status XML for device name -> {e}")
    else:
        try:
            name = soup.userinterface.find('name').text
        except AttributeError:
            raise Exception("Could not find 'name' in status XML")
        else:
            obj.device_name = str(name)

def _get_number_of_panels(obj):
    try:
        soup = bs4.BeautifulSoup(obj.status_xml, features='lxml')
    except Exception as e:
        raise Exception(f"Issue trying to parse status XML for number of panels -> {e}")
    else:
        devices = soup.find_all("connecteddevice")
        obj.number_of_panels = 0
        for device in devices:
            try:
                name = device.find('name').text
            except AttributeError:
                # only way to skip
                pass
            else:
                if name == "Cisco TelePresence Touch":
                    if device.status.text == "Connected":
                        obj.number_of_panels += 1
        if obj.number_of_panels == 0:
            obj.number_of_panels = None

def _get_sw_version(obj):
    try:
        soup = bs4.BeautifulSoup(obj.status_xml, features='lxml')
    except Exception as e:
        raise Exception(f"Issue trying to parse status XML for software version -> {e}")
    try:
        sw = soup.find("systemunit").software.version.text
    except AttributeError:
       return
    else:
        obj.sw_version = sw

        
def _get_device_type(obj):
    try:
        soup = bs4.BeautifulSoup(obj.status_xml, features='lxml')
    except Exception as e:
        raise Exception(f"Issue trying to parse status XML for device type -> {e}")
    try:
        hw = soup.find("systemunit").productid.text
    except AttributeError:
       return
    else:
        obj.device_type = hw

def _get_sip_uri(obj):
    try:
        soup = bs4.BeautifulSoup(obj.status_xml, features='lxml')
    except Exception as e:
        raise Exception(f"Issue trying to parse status XML for address -> {e}")
    else:
        # ridiculous non standard xml tags...
        try:
            uri = soup.find("sip").primary.uri.text
        except AttributeError:
            try:
                uri = soup.find('registration').uri.text
            except AttributeError:
                try:
                    uri = soup.find('contactinfo').number.text
                except AttributeError:
                    raise Exception("Could not find 'sip uri' in status XML")
                else:
                    obj.sip_uri = uri
            else:
                obj.sip_uri = uri
        else:
            obj.sip_uri = uri

# -- hw/sw checker for macro capability

def _get_macro_capable(obj):
        if obj.device_type == 'Cisco TelePresence SX10' or obj.sw_version.startswith('ce8') or obj.sw_version.startswith('TC7'):
            obj.macro_capable = False
        else:
            obj.macro_capable = True
