import requests

# get rid of pesky warnings
requests.packages.urllib3.disable_warnings()

def get(self, uri):
    if self.session_cookie is None:
        raise Exception("No cookie available, run .get_cookie()")
    url = f'https://{self.ip}/{uri}'
    try:
        r = requests.get(url, cookies=self.session_cookie,verify=False, timeout=self.timeout)
    except requests.exceptions.ConnectTimeout as e:
        self.online = False
        raise Exception(f"{self.ip} appears to be offline!")
    except requests.exceptions.ConnectionError as e:
         raise Exception(f"{self.ip} https GET request failed! -> {e}")
    else:
        self.online = True
        if r.status_code != 200:
            if r.status_code == 404:
                raise Exception(f"uri `{uri}` not found!")
            else:    
                raise Exception(f"Issue with api call -> {r.content.decode()}")
        else:
            response = r.content.decode()
            if response.startswith("<!DOCTYPE html>"):
                raise CookieExpired()
            else:
                return response
        
def post(self, payload):
    """ Returns XML content from device """
    if self.session_cookie is None:
        raise Exception("No cookie available, run .get_cookie()")
    url = f'https://{self.ip}/putxml'
    try:
        r = requests.post(url, cookies=self.session_cookie, data=payload, verify=False, timeout=self.timeout)
    except requests.exceptions.ConnectTimeout as e:
        self.online=False
        raise Exception(f"{self.ip} appears to be offline!")
    except requests.exceptions.ConnectionError as e:
         raise Exception(f"{self.ip} https POST request failed! -> {e}")
    else:
        self.online = True
        response = r.content.decode()
        if r.status_code != 200:
            if r.status_code == 404:
                raise Exception(f"uri `{uri}` not found!")
            elif r.status_code == 401 and self.password_verified:
                raise CookieExpired(response)
            else:    
                raise Exception(f"Issue with api call -> {r.content.decode()}")
        else:
            if response.startswith("<!DOCTYPE html>"):
                raise CookieExpired(response)
            elif '<Reason>Unknown command</Reason>' in response:
                start = response.find('<XPath>')
                end = response.find('</XPath>')
                command = response[start+7:end]#add 7 for <Xpath>
                raise Exception(f"Codec does not support this command -> {command}")
            elif response == '<?xml version="1.0"?>\n<Command/>\n':
                raise Exception(f"Codec returned null value for -> {payload}")
            else:
                return response

def get_cookie(self):
    auth = requests.auth.HTTPBasicAuth(self.user, self.password)
    try:
        session = requests.post(f'https://{self.ip}/xmlapi/session/begin',auth=auth, verify=False, timeout=self.timeout)
    except requests.exceptions.ConnectTimeout as e:
        self.online=False
        raise Exception(f"{self.ip} appears to be offline! -> {e}")    
    except requests.exceptions.ConnectionError as e:
        self.online = False
        raise Exception(f"{self.ip} connection error -> {e}")
    else:
        self.online = True
        # Set a flag for password, store the cookie
        if session.status_code == 204:
            self.password_verified = True
            try:
                self.session_cookie=session.cookies.get_dict()
            except KeyError:
                raise Exception(f"Issue when opening cookie as Dict: {self.session_cookie}")
            return self.session_cookie
        elif session.status_code == 200:
            self.password_verified = False
            self.session_cookie = None
            self.macro_capable = False # no XMLAPI means no macros!
            raise Exception(f"https request successful, but no cookie in response")
        elif session.status_code == 401:
            self.password_verified = False
            self.session_cookie = None
            raise Exception(f"Credentials ({self.user}:{self.password}) incorrect.")
        else:
            raise Exception(f"Cookie request failed -> {session.content.decode()}")

def close_session(self):
    if self.session_cookie is not None:
        try:
            session = requests.post(f'https://{self.ip}/xmlapi/session/end', cookies=self.session_cookie,verify=False, timeout=self.timeout)
        except requests.exceptions.ConnectTimeout as e:
            self.online=False
            raise Exception(f"{self.ip} appears to be offline! -> {e}")    
        except requests.exceptions.ConnectionError as e:
            self.online = False
            raise Exception(f"{self.ip} connection error -> {e}")
        else:
            self.session_cookie = None
            if session.status_code == 204:
                return True
            elif session.status_code == 200:
                return "Session cookie did not exist"
            else:
                raise Exception(f"Something went wrong when closing the session.\n{session.content.decode()}")
    else:
        return "Codec does not have a cookie"

# Error handling
class CookieExpired(Exception):

    def __init__(self, message="Cookie is expired, run .get_cookie() to get a new one"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"        
        
        
