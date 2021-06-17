import bs4
import os

def get_config(self):
    self.configuration_xml = self.get('configuration.xml')
    _get_macros_enabled(self)
    _get_macros_autostart(self)
    _get_macro_details(self)
    _get_extensions(self)
    return self.configuration_xml

def get_status(self):
    self.status_xml = self.get('status.xml')
    _get_device_name(self)
    _get_number_of_panels(self)
    _get_sw_version(self)
    _get_device_type(self)
    return self.status_xml

# -- Upload/Delete -- #

def upload_macro(self, filename, macro_name):
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

def create_user(self, username, password, role):
    payload = f'''<Command><UserManagement><User><Add>
    <Active>True</Active>
    <PassphraseChangeRequired>False</PassphraseChangeRequired>
    <Passphrase>{password}</Passphrase>
    <Role>{role}</Role>
    <YourPassphrase>{self.password}</YourPassphrase>
    <Username>{username}</Username>
    </Add></User></UserManagement></Command>'''
    return self.post(payload)

def delete_user(self, username):
    payload = f'''<Command><UserManagement><User><Delete>
    <YourPassphrase>{self.password}</YourPassphrase>
    <Username>{username}</Username>
    </Delete></User></UserManagement></Command>'''
    return self.post(payload)

# -- Macro Setting Commands -- #

def enable_macros(self, mode='on'):
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
    if mode in ['on','off']:
        p = self.put_xml(f'<?xml version="1.0"?><Configuration><Macros><Autostart>{mode}</Autostart></Macros></Configuration>')
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


# ---- PRIVATE METHODS ---- #

# -- configuration XML parsing -- #

def _get_macros_enabled(obj):
    try:
        soup = bs4.BeautifulSoup(obj.configuration_xml, features='lxml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
    try:
        macros = soup.find("macros").mode.text
    except AttributeError:
        raise Exception("Could not find macros attribute in config xml")
    else:
        if macros == 'On':
            obj.macros_enabled = True
        if macros == 'Off':
            obj.macros_enabled = False
    return obj.macros_enabled

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
        return obj.macros_autostart

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
                raise Exception(f'Issue parsing XML -> {e}')
            else:
                obj.macro_names = [mac['name'] for mac in obj.macro_details]
                for macro in obj.macro_details:
                    macro_code = obj.post(f'<Command><Macros><Macro><Get><Name>{macro["name"]}</Name><Content>True</Content></Get></Macro></Macros></Command>')
                    try:
                        soup = bs4.BeautifulSoup(macro_code, features='xml')
                    except Exception as e:
                        raise Exception(f'Issue parsing XML -> {e}')
                    macro['code'] = soup.Content.text
        else:
            obj.macro_details = None
            obj.macro_names = None
        return (obj.macro_names, obj.macro_details)

def _get_extensions(obj):
    """ Returns a list containing dicts with keys "panel_id" and "xml" """
    # !! uses 'xml' parser vs 'lxml' !! #
    ext = obj.post('<Command><UserInterface><Extensions><List/></Extensions></UserInterface></Command>')
    try:
        soup = bs4.BeautifulSoup(ext, features='xml')
    except Exception as e:
        raise Exception(f'Issue parsing XML -> {e}')
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
            return obj.extension_details
        else:
            obj.extension_details = None
            return

# -- Status XML parsing -- #

def _get_device_name(obj):
    try:
        soup = bs4.BeautifulSoup(obj.status_xml, features='lxml')
    except Exception as e:
        raise Exception(f"Issue trying to parse status XML -> {e}")
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
        raise Exception(f"Issue trying to parse status XML -> {e}")
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
        raise Exception(f"Issue trying to parse status XML -> {e}")
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
        raise Exception(f"Issue trying to parse status XML -> {e}")
    try:
        hw = soup.find("systemunit").productid.text
    except AttributeError:
       return
    else:
        obj.device_type = hw