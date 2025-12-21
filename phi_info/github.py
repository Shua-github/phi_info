from github import Github, Auth, UnknownObjectException
from github.GitRelease import GitRelease
from github.Repository import Repository
from remotezip import RemoteZip
from phi_info.taptap import TapTapClient, PHI_ID
from phi_info.unity import from_files_and_typetree
import os
import json
import pathlib

TMP_DIR = pathlib.Path("./tmp")
TMP_DIR.mkdir(exist_ok=True)


def check_update(repo: Repository, version: str) -> bool:
    print("[CHECK] Checking latest GitHub release...")
    try:
        release = repo.get_latest_release()
        print(f"[CHECK] Latest release tag: {release.tag_name}")
    except UnknownObjectException:
        print("[CHECK] No release found, treating as first release")
        return True
    return release.tag_name != version

def github_main():
    print("[INIT] Initializing GitHub client")
    gh = Github(auth=Auth.Token(os.getenv("GITHUB_TOKEN")))
    repo = gh.get_repo(os.getenv("GITHUB_REPOSITORY"))
    print(f"[INIT] Repository loaded: {repo.full_name}")

    print("[INIT] Initializing TapTap client")
    taptap = TapTapClient(PHI_ID)
    current_version = taptap.version
    print(f"[INFO] Current APK version: {current_version}")

    if not check_update(repo, current_version):
        print("[SKIP] No update detected, exiting")
        return

    print("[UPDATE] New version detected, preparing update")

    apk_info = taptap.apk_info
    if not apk_info.apk.download:
        raise RuntimeError("APK download url not found")

    print("[LOAD] Loading typetree configuration")
    with open("./resources/typetree.json", encoding="utf8") as f:
        typetree = json.load(f)["GameInformation"]

    files = {}
    print("[PARSE] Reading APK and extracting song data")
    with RemoteZip(apk_info.apk.download) as apk:
        for file in ["assets/bin/Data/globalgamemanagers.assets","assets/bin/Data/level0"]:
            files[file] = apk.read(file)
    
    csv_str = from_files_and_typetree(files, typetree)

    csv_name = "song_list.csv"
    csv_path = TMP_DIR / csv_name
    print(f"[OUTPUT] Writing CSV to {csv_path}")
    with open(csv_path, "w", encoding="utf8") as out:
        out.write(csv_str)

    print("[GITHUB] Creating release and uploading asset")
    commit_sha = repo.get_branch("main").commit.sha
    msg = "Phigros Version:" + current_version

    release: GitRelease = repo.create_git_tag_and_release(
        tag=current_version,
        tag_message=msg,
        object=commit_sha,
        type="commit",
        release_name=current_version,
        release_message=msg,
    )

    release.upload_asset(str(csv_path), name=csv_name)
    print("[DONE] Release created and asset uploaded successfully")

    gh.close()
    print("[CLEANUP] GitHub client closed")


if __name__ == "__main__":
    import time
    start_time = time.time()
    print("[START] Script started")
    github_main()
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"[END] Script finished in {elapsed:.2f} seconds")