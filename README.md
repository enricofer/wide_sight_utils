## Widesight massive uploader.

Install requirements
First process raw equirectangular images to bind proper exif tags
Then upload the images to widesight backend service (https://github.com/enricofer/wide_sight)

```
Usage:
  pip install -r requirements.txt
  python ws_uploader.py process FOLDER_PATH --gpx=PATH [--csv=PATH --telemetry=PATH --delay=MILLISECONDS]
  python ws_uploader.py upload FOLDER_PATH (--new_sequence=TITLE | --sequence=ID) --user=USER --password=PASSWORD --backend=URL [--height=H]
  python ws_uploader.py -h | --help
  python ws_uploader.py --version

Arguments:
  FOLDER_PATH              Images directory path

Options:
  -h --help                Show this screen.
  --backend=URL            Backend service base url
  --user=USER              User
  --password=PASSWORD      Password
  --new_sequence=TITLE     Create new sequence container titled with TITLE
  --sequence=ID            Sequence container
  --height=H               Height from ground of camera [default: 2]
  --gpx=PATH               Gpx file path
  --csv=PATH               CSV with frames instant time (experimental)
  --telemetry=PATH         Telemetry csv path (experimental)
  --delay=MILLISECONDS     Delay adjust in milliseconds [default: 0]
```

