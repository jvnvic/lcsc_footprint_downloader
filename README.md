# LCSC KiCad Exporter

A modern web app to download KiCad-compatible **symbols**, **footprints**, and **3D STEP models** from [LCSC/JLCPCB](https://lcsc.com) part numbers.

Simple interface, fast in-memory processing, and one-click `.zip` export for your convenience.

---

![Screenshot of the app](https://i.imgur.com/vcv36CX.jpeg)


---

## Features

- Enter any `LCSC ID` (e.g. `C2040`)
- Download individually:
  - 🔹 KiCad Symbol (`.kicad_sym`)
  - 🔹 KiCad Footprint (`.kicad_mod`)
  - 🔹 3D STEP model (`.step`)
- Or click **"Download All as ZIP"** for everything at once
- Fully in-memory file handling (no temp file writes on server)
- Clean, dark-themed UI with orange accent color

---

## Hosted Online

[Open the app](https://lcscfootprintdownloader.onrender.com/)  

---

## Built With

- Python + [Flask](https://flask.palletsprojects.com/)
- [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py)
- Deployed on [Render](https://render.com)

---

## Credits

- Forked from [**wormyrocks**](https://github.com/wormyrocks/lcsc_step_downloader)
- Based on [**easy2kicad**](https://github.com/uPesy/easyeda2kicad.py)
- By **Daniel Jovanovic**

---

## License

MIT – use freely, modify openly.
