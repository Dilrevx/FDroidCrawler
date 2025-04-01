import io
import scrapy
import xml.etree.ElementTree as ET
import json
from pathlib import Path

CRAWLER_ROOT = Path(__file__).parent.parent.resolve()
ASSET_ROOT = CRAWLER_ROOT / "assets"
ASSET_ROOT.mkdir(parents=True, exist_ok=True)


def parse_fdroid_xml(xml_content: str):
    """
    crawl the xml at https://f-droid.org/repo/index.xml
    and parse the xml file to get the app information
    """
    tree = ET.parse(io.StringIO(xml_content))
    root = tree.getroot()

    # 解析仓库元数据
    repo = root.find("repo")
    repo_data = {
        "name": repo.get("name"),
        "pubkey": repo.get("pubkey"),
        "url": repo.get("url"),
        "timestamp": repo.get("timestamp"),
        "version": repo.get("version"),
        "description": repo.find("description").text,
        "mirrors": [m.text for m in repo.findall("mirror")],
    }

    applications = []

    # 遍历所有应用
    for app in root.findall("application"):
        # 解析应用基本信息
        app_data = {
            "id": app.get("id"),
            "name": app.findtext("name"),
            "added": app.findtext("added"),
            "last_updated": app.findtext("lastupdated"),
            "summary": app.findtext("summary"),
            "desc": "".join(app.find("desc").itertext()).strip(),  # HTML
            "license": app.findtext("license"),
            "categories": [c.text for c in app.findall("category")],
            "source": app.findtext("source"),
            "tracker": app.findtext("tracker"),
            "author": app.findtext("author"),
            "anti_features": [af.text for af in app.findall("antifeatures")],
            "icon": app.findtext("icon"),
            "changelog": app.findtext("changelog"),
            "email": app.findtext("email"),
            "marketversion": app.findtext("marketversion"),
            "marketvercode": app.findtext("marketvercode"),
            "antifeatures": app.findtext("antifeatures"),
        }
        packages = []

        # 解析所有包版本
        for pkg in app.findall("package"):
            pkg_data = {
                "version": pkg.findtext("version"),
                "version_code": pkg.findtext("versioncode"),
                "apk_name": pkg.findtext("apkname"),
                "apk_hash": pkg.findtext("hash"),
                "apk_size": pkg.findtext("size"),
                "sdk_version": pkg.findtext("sdkver"),
                "target_sdk": pkg.findtext("targetSdkVersion"),
                "permissions": pkg.findtext("permissions"),
                "signature": pkg.findtext("sig"),
                "added_date": pkg.findtext("added"),
            }
            packages.append(pkg_data)

        app_data["packages"] = packages
        applications.append(app_data)
    return {
        "repository": repo_data,
        "applications": applications,
    }


from xml.etree.ElementTree import iterparse


from scrapy import http


class RepoIndexSpider(scrapy.Spider):
    name = "repo-index"
    allowed_domains = ["."]
    start_urls = ["https://f-droid.org/repo/index.xml"]

    def parse(self, response: http.XmlResponse):
        xml_file = ASSET_ROOT / "index.xml"
        repo_file = ASSET_ROOT / "repo.json"
        application_file = ASSET_ROOT / "applications.json"

        xml_file.write_text(response.text, encoding="utf-8")

        dict_ = parse_fdroid_xml(response.text)
        repo_data = dict_["repository"]
        app_data = dict_["applications"]

        repo_file.write_text(
            json.dumps(repo_data, indent=4, ensure_ascii=False), encoding="utf-8"
        )

        yield from app_data
