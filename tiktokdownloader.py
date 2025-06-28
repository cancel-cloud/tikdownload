import os
import csv
import sys
import datetime
import requests
import re
import signal
from urllib.parse import urlparse
import yt_dlp

# Globaler Flag, um Interrupts zu signalisieren
stop_requested = False

def signal_handler(signum, frame):
    global stop_requested
    stop_requested = True
    print("\nInterrupt signal received. Die aktuelle Zeile wird zu Ende verarbeitet und der Fortschritt gespeichert.")

signal.signal(signal.SIGINT, signal_handler)

def sanitize_filename(filename):
    # Entfernt ungültige Zeichen aus Dateinamen
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
    return sanitized.strip().replace(" ", "_")

def download_video(url, output_folder):
    ydl_opts = {
        'outtmpl': os.path.join(output_folder, '%(id)s.%(ext)s'),
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extrahiere Informationen und lade das Video herunter
        info = ydl.extract_info(url, download=True)
    return info

def download_image(url, output_folder, filename):
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        path = urlparse(url).path
        # Ermittele Dateiendung und entferne ggf. ungültige Zeichen (z.B. ':')
        ext = os.path.splitext(path)[1].replace(":", "") if os.path.splitext(path)[1] else '.jpg'
        file_path = os.path.join(output_folder, filename + ext)
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
    except Exception as e:
        raise Exception(f"Image download error: {e}")

def main():
    csv_filename = input("Bitte gib den Namen der CSV-Datei ein (z.B. example.csv): ").strip()
    if not os.path.exists(csv_filename):
        print(f"Fehler: Datei '{csv_filename}' nicht gefunden.")
        sys.exit(1)

    # Erstelle Ausgabeverzeichnis basierend auf dem aktuellen Datum
    date_str = datetime.datetime.now().strftime("%d-%m-%Y")
    output_folder = f"favorites-{date_str}"
    os.makedirs(output_folder, exist_ok=True)
    print(f"Erstelle Ausgabeverzeichnis: {output_folder}")

    # Fortschrittsspeicherung: Prüfe, ob es eine progress.txt gibt
    progress_file_path = os.path.join(output_folder, "progress.txt")
    resume_row = 0
    if os.path.exists(progress_file_path):
        with open(progress_file_path, "r", encoding="utf-8") as pf:
            try:
                resume_row = int(pf.read().strip())
            except:
                resume_row = 0
        answer = input(f"Fortschritt gefunden: Ab Zeile {resume_row+1} fortfahren? (j/n): ").strip().lower()
        if answer != "j":
            resume_row = 0

    # Fehler werden in download_errors.csv protokolliert
    error_csv_path = os.path.join(output_folder, "download_errors.csv")
    error_file = open(error_csv_path, "w", newline="", encoding="utf-8")
    error_writer = csv.writer(error_file)
    error_writer.writerow(["row", "url", "error"])

    video_title_mappings = []  # Speichert Mapping-Daten für Videos
    last_processed_row = resume_row

    try:
        with open(csv_filename, 'r', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            current_row = 0
            for row in reader:
                current_row += 1
                if current_row <= resume_row:
                    continue
                # Verarbeite alle URL-Felder in der Zeile
                for key, value in row.items():
                    if value and value.startswith("http"):
                        url = value.strip()
                        try:
                            # Behandle als Video, wenn "/video/" in der URL vorkommt
                            if "tiktok.com" in url and "/video/" in url:
                                print(f"[Video {current_row}] Lade Video von {url} herunter")
                                info = download_video(url, output_folder)
                                filename = f"{info['id']}.{info['ext']}"
                                video_title_mappings.append({
                                    "row": current_row,
                                    "url": url,
                                    "old_filename": filename,
                                    "title": info.get("title", "")
                                })
                            # Behandle als Bild, wenn:
                            # - "photo" in der URL vorkommt
                            # - bekannte Bild-Endungen vorhanden sind
                            # - oder wenn es sich um eine TikTokCDN-URL handelt, die "obj/tos" enthält und KEINE Dateiendung im Pfad hat
                            elif ("photo" in url.lower() or
                                  any(ext in url.lower() for ext in [".avif", ".jpg", ".jpeg", ".png", ".gif"]) or
                                  ("tiktokcdn.com" in url.lower() and "obj/tos" in url.lower() and os.path.splitext(urlparse(url).path)[1] == "")):
                                print(f"[Bild {current_row}] Lade Bild von {url} herunter")
                                filename = f"row{current_row}_{key}"
                                download_image(url, output_folder, filename)
                            else:
                                print(f"[Video {current_row}] Unbekannter Medientyp, versuche Video-Download von {url}")
                                info = download_video(url, output_folder)
                                filename = f"{info['id']}.{info['ext']}"
                                video_title_mappings.append({
                                    "row": current_row,
                                    "url": url,
                                    "old_filename": filename,
                                    "title": info.get("title", "")
                                })
                        except Exception as e:
                            error_writer.writerow([current_row, url, str(e)])
                            print(f"Fehler in Reihe {current_row} bei URL {url}: {e}")
                last_processed_row = current_row
                # Prüfe nach jeder Zeile, ob ein Interrupt angefordert wurde
                if stop_requested:
                    print("Interrupt angefordert. Speichere Fortschritt und beende.")
                    with open(progress_file_path, "w", encoding="utf-8") as pf:
                        pf.write(str(last_processed_row))
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        print("Download wurde durch den Benutzer unterbrochen.")
    finally:
        error_file.close()

    # Bei normalem Abschluss wird progress.txt gelöscht
    if not stop_requested and os.path.exists(progress_file_path):
        os.remove(progress_file_path)

    # Speichere die Video-Titel-Mappings in video_titles.csv
    mapping_csv_path = os.path.join(output_folder, "video_titles.csv")
    with open(mapping_csv_path, "w", newline="", encoding="utf-8") as mapping_file:
        mapping_writer = csv.writer(mapping_file)
        mapping_writer.writerow(["row", "url", "old_filename", "title"])
        for mapping in video_title_mappings:
            mapping_writer.writerow([mapping["row"], mapping["url"], mapping["old_filename"], mapping["title"]])
    print("Download abgeschlossen.")

    # Frage, ob die Videos umbenannt werden sollen
    if video_title_mappings:
        answer = input("Möchtest du die Dateinamen der Videos in die auf TikTok angezeigten Titel umändern? (j/n): ").strip().lower()
        if answer == "j":
            for mapping in video_title_mappings:
                old_path = os.path.join(output_folder, mapping["old_filename"])
                new_title = sanitize_filename(mapping["title"])
                ext = os.path.splitext(mapping["old_filename"])[1]
                new_filename = new_title + ext
                new_path = os.path.join(output_folder, new_filename)
                try:
                    os.rename(old_path, new_path)
                    print(f"Datei umbenannt: {mapping['old_filename']} -> {new_filename}")
                except Exception as e:
                    print(f"Fehler beim Umbenennen von {mapping['old_filename']}: {e}")
            print("Umbenennen abgeschlossen.")
        else:
            print("Umbenennen übersprungen.")

if __name__ == "__main__":
    main() 