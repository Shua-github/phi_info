import json
import zipfile
import csv
import io
from UnityPy import Environment


def export_song_info_from_game_info(game_info: dict) -> str:
    output = []
    songs_section = game_info.get("song", {})
    combo_dict = {
        combo["songsId"]: combo for combo in game_info.get("songAllCombos", [])
    }

    for _, songs_list in songs_section.items():
        for song in songs_list:
            song_id = song.get("songsId")
            if not song_id:
                continue

            all_combo_num = combo_dict.get(song_id, {}).get("allComboNum", [])
            levels = song.get("levels", [])
            charters = song.get("charter", [])
            difficulties = song.get("difficulty", [])

            level_dict = {}

            for i, difficulty in enumerate(difficulties):
                if difficulty == 0.0:
                    continue
                level_name = levels[i]
                level_dict[level_name] = {
                    "c": charters[i],
                    "a": all_combo_num[i] if i < len(all_combo_num) else 0,
                    "d": round(difficulty, 1),
                }

            if not level_dict:
                continue

            output.append(
                {
                    "id": song_id,
                    "name": song.get("songsName", ""),
                    "composer": song.get("composer", ""),
                    "illustrator": song.get("illustrator", ""),
                    "preview_time": round(song.get("previewTime", 0), 2),
                    "preview_end_time": round(song.get("previewEndTime", 0), 2),
                    "levels": json.dumps(
                        level_dict, ensure_ascii=False, separators=(",", ":")
                    ),
                }
            )

    fieldnames = [
        "id",
        "name",
        "composer",
        "illustrator",
        "preview_time",
        "preview_end_time",
        "levels",
    ]
    output_io = io.StringIO()
    writer = csv.DictWriter(output_io, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output)

    return output_io.getvalue()


def from_apk_and_typetree(file: io.BytesIO, typetree: dict) -> str:
    env = Environment()
    with zipfile.ZipFile(file) as apk:
        env.load_file(
            apk.read("assets/bin/Data/globalgamemanagers.assets"),
            name="assets/bin/Data/globalgamemanagers.assets",
        )
        env.load_file(apk.read("assets/bin/Data/level0"))

    game_info = None
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        data = obj.read()
        if data.m_Script.get_obj().read().name == "GameInformation":
            game_info = obj.read_typetree(typetree)
            break

    return export_song_info_from_game_info(game_info)


def unity_main():
    import sys

    with open("./resources/typetree.json", encoding="utf8") as f:
        typetree = json.load(f)["GameInformation"]

    if len(sys.argv) < 2:
        print("Usage: <apk_path>")
        sys.exit(1)

    apk_path = sys.argv[1]

    with open(apk_path, "rb") as f:
        apk_bytes = io.BytesIO(f.read())

    csv_str = from_apk_and_typetree(apk_bytes, typetree)

    with open("output.csv", "w", encoding="utf8") as out:
        out.write(csv_str)


if __name__ == "__main__":
    unity_main()
