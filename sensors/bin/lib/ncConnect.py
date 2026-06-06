# module to connect to nextcloud
import os, requests

class myNextcloud:
    def __init__(self, **kwargs):
        self.url      = kwargs.get("url",os.getenv("NEXTCLOUD_URL"))
        self.user     = kwargs.get("user",os.getenv("NEXTCLOUD_USER"))
        self.apitoken = kwargs.get("apitoken",os.getenv("NEXTCLOUD_APITOKEN"))
        
    def getFile(self,path):
        url = f"{self.url}/remote.php/dav/files/{self.user}{path}"
        response = requests.get(url, auth=(self.user, self.apitoken))
        try:
            response.raise_for_status()
            result = response.text

        except requests.RequestException as e:
            print(f"Fail download {url}: {e}")
            result = ""

        return result
    
    def putFile(self,path,content):
        url = f"{self.url}/remote.php/dav/files/{self.user}{path}"
        response = requests.put(url, auth=(self.user, self.apitoken), data=content.encode("utf-8"))

        if response.status_code in (200, 201, 204):
            return True
        else:
            print(f"Fail upload {url}: {response.status_code}")
            print(response.text)
            return False

    def putFileFromFile(self,path,srcpath):
        with open(srcpath,'r',encoding="utf-8") as f:
            text = f.read()
            return self.putFile(path,text)
        
        return False


