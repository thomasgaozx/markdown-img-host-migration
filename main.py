import os
import re
import json
import glob
import string
import requests

MD_IMG = re.compile("!\\[(?P<img_name>.*)\\]\\((?P<img_url>.+)\\)") # tested at `regex101.com/r/Hd3foB/8`
URL_VALID = re.compile( # source: stackoverflow.com/a/7160778/172132
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
NON_WORD = re.compile("\W+")
IMG_INFO_FILE = "imginfo.json"

def download_img(img_url, file_name):
    """download the image"""
    log2("downloading {} from {} ...".format(file_name, img_url))
    response = requests.get(img_url)
    if not response.ok:
        log("failed, cannot download from " + img_url)
        return False

    with open(file_name, 'wb') as handler:
        handler.write(response.content)
    return True

def url_is_valid(url):
    return URL_VALID.fullmatch(url) != None

def rename_img(img_name):
    return NON_WORD.sub('', img_name.replace("-", "_"))
    
def log(msg):
    """level 1 logging"""
    print(msg)

def log1(msg):
    """level 2 logging"""
    print("  " + msg)

def log2(msg):
    """level 3 logging"""
    print("    " + msg)

class ImageServerMigration(object):
    def __init__(self, project_root, img_folder="image"):
        self.proj_dir = project_root
        self.img_dir = img_folder
        self.imginfo = dict() # { img_url : downloaded_name }

        if os.path.exists(IMG_INFO_FILE):
            log("loading img info ...")
            with open(IMG_INFO_FILE, 'r') as json_file:
                self.imginfo = json.load(json_file)

        if not os.path.exists(self.img_dir):
            log("creating '{}/' ...".format(self.img_dir))
            os.mkdir(self.img_dir)

    def download_photos_from_all(self):
        mds = glob.glob(os.path.join(self.proj_dir, "**\\*.md"), recursive=True)
        log("found the following markdown files: " + ", ".join(mds))

        for md in mds:
            log1("processing {} ...".format(md))
            with open(md, 'r', encoding="utf-8") as mdfile:
                self._download_photos_from_md(mdfile)

        log("download complete, updating img info on disk ...")
        with open(IMG_INFO_FILE, 'w', encoding="utf-8") as json_file:
            json.dump(self.imginfo, json_file, indent=4)

    def relabelling_effort(self, host_img_root_dir):
        """
        Assume the path to the images is `$host_img_root_dir$/$img_name$`
        For this reason, do not use Google Drive as the new image server
        because the endpoint to the file is hashed.
        """
        mds = glob.glob(os.path.join(self.proj_dir, "**\\*.md"), recursive=True)
        log("found the following markdown files: " + ", ".join(mds))

        for md in mds:
            log1("reading {} ...".format(md))
            with open(md, 'r', encoding="utf-8") as mdfile:
                new_content = "".join(self._relabelling_line(line, host_img_root_dir)
                    for line in mdfile)
    
            log1("writing {} ...".format(md))
            with open(md, 'w', encoding="utf-8") as mdfile:
                mdfile.write(new_content)
        
        log("relabelling complete, updating img info on disk ...")
        with open(IMG_INFO_FILE, 'w') as json_file:
            json.dump(self.imginfo, json_file, indent=4)
    
    def _relabelling_line(self, line, host_img_root_dir):
        result = MD_IMG.search(line)
        if result:
            log2("discovered: " + line.strip())
            old_url = result.group('img_url')

            dname = self.imginfo.get(old_url)
            if dname: # not None
                new_url = os.path.join(host_img_root_dir, dname + ".png")
                
                log2("matched with image filename '{}', relabelling to '{}' ...".format(
                    dname, new_url))

                self.imginfo[new_url] = self.imginfo.pop(old_url)
                return line.replace(old_url, new_url)
        return line

    def _download_photos_from_md(self, mdfile):
        """
        imginfo - write
        mdfile - read

        search in mdfile occurrences of images and download
        """
        for line in mdfile:
            result = MD_IMG.search(line)
            if result: # line contains an image
                log2("discovered: " + line.strip())
                
                img_name = rename_img(result.group('img_name'))
                img_url = result.group('img_url')
                if url_is_valid(img_url) and self.imginfo.get(img_url) == None:
                    log2("'{}' has valid url and hasn't been downloaded already".format(img_name))

                    duplications = { fname for fname in os.listdir(self.img_dir)
                        if fname.startswith(img_name)}
                    if img_name in duplications: # handle duplicate image names
                        img_name = "{}({})".format(img_name,
                            1+sum(1 for d in duplications if d[len(img_name)]=='(')
                        )

                    if (download_img(img_url, "{}/{}.png".format(self.img_dir, img_name)))
                        self.imginfo[img_url] = img_name
