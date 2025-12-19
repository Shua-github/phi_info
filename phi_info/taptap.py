import hashlib
import httpx
import random
import string
import time
import urllib.parse
import uuid
from dataclasses import dataclass

sample = string.ascii_lowercase + string.digits


@dataclass
class ApkFile:
    native_code: list[str]
    name: str
    size: int
    md5: str
    version_code: int
    version_name: str
    download: str | None = None


@dataclass
class DownloadInfo:
    apk_id: int
    apk: ApkFile
    api_level: int
    is_force: bool
    target_sdk_version: int


@dataclass
class ApkDetailResponse:
    apk_id: int
    apk: ApkFile


class TapTapClient:
    def __init__(self, app_id: int):
        self.app_id = app_id
        self.uid: uuid.UUID
        self.X_UA: str
        self.download_info: DownloadInfo
        self._init_app_info()

    def _init_app_info(self) -> None:
        self.uid = uuid.uuid4()
        self.X_UA = (
            "V=1&PN=TapTap&VN=2.40.1-rel.100000&VN_CODE=240011000&"
            "LOC=CN&LANG=zh_CN&CH=default&UID=%s&NT=1&SR=1080x2030&"
            "DEB=Xiaomi&DEM=Redmi+Note+5&OSV=9" % self.uid
        )

        url = (
            f"https://api.taptapdada.com/app/v2/detail-by-id/{self.app_id}?"
            f"X-UA={urllib.parse.quote(self.X_UA)}"
        )
        headers = {"User-Agent": "okhttp/3.12.1"}

        with httpx.Client() as client:
            r = client.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()["data"]["download"]

        apk = ApkFile(**data["apk"])

        self.download_info = DownloadInfo(
            apk_id=data["apk_id"],
            apk=apk,
            api_level=data["api_level"],
            is_force=data["is_force"],
            target_sdk_version=data["target_sdk_version"],
        )

    @property
    def apk_info(self) -> ApkDetailResponse:
        nonce = "".join(random.sample(sample, 5))
        t = int(time.time())

        param = (
            "abi=arm64-v8a,armeabi-v7a,armeabi&"
            f"id={self.download_info.apk_id}&"
            f"node={self.uid}&nonce={nonce}&sandbox=1&"
            f"screen_densities=xhdpi&time={t}"
        )

        sign_src = f"X-UA={self.X_UA}&{param}PeCkE6Fu0B10Vm9BKfPfANwCUAn5POcs"
        sign = hashlib.md5(sign_src.encode()).hexdigest()
        body = f"{param}&sign={sign}"

        url = (
            "https://api.taptapdada.com/apk/v1/detail?"
            f"X-UA={urllib.parse.quote(self.X_UA)}"
        )
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "okhttp/3.12.1",
        }

        with httpx.Client() as client:
            r = client.post(url, content=body.encode(), headers=headers)
            r.raise_for_status()
            data = r.json()["data"]

        apk = ApkFile(**data["apk"])
        return ApkDetailResponse(apk_id=data["apk_id"], apk=apk)

    @property
    def version(self):
        return f"v{self.apk_info.apk.version_name}-{self.apk_info.apk.version_code}"


PHI_ID = 165287


def taptap_main():
    client = TapTapClient(PHI_ID)
    print("Download Info:", client.download_info)

    apk_info = client.apk_info
    print("APK Info:", apk_info)


if __name__ == "__main__":
    taptap_main()
