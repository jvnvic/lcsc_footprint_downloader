from flask import Flask, send_file, request, abort
from io import BytesIO
import json

from easyeda2kicad.easyeda_api import EasyedaApi
from easyeda2kicad.easyeda_importer import (
    Easyeda3dModelImporter,
    EasyedaFootprintImporter,
    EasyedaSymbolImporter,
)
from easyeda2kicad.export_kicad_footprint import ExporterFootprintKicad
from easyeda2kicad.export_kicad_symbol import ExporterSymbolKicad

app = Flask(__name__)


def get_lcsc_component_data(lcsc_id):
    try:
        api = EasyedaApi()
        cad_data = api.get_cad_data_of_component(lcsc_id=lcsc_id)

        model = Easyeda3dModelImporter(cad_data, download_raw_3d_model=False).create_3d_model()
        footprint = EasyedaFootprintImporter(cad_data).get_footprint()
        symbol = EasyedaSymbolImporter(cad_data).get_symbol()

        name = model.name if model else footprint.info.name
        step_data = api.get_step_3d_model(model.uuid) if model else None

        return name, step_data, footprint, symbol
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None, None


@app.route("/get_model", methods=["GET"])
@app.route("/get_model/<lcsc_id>", methods=["GET"])
def get_model(lcsc_id=None):
    if not lcsc_id:
        lcsc_id = request.args.get("lcsc_id")
    if not lcsc_id:
        return "LCSC ID is required", 400

    download_type = request.args.get("type", "step")  # step, symbol, footprint, kicad_mod, kicad_sym

    name, step_data, footprint, symbol = get_lcsc_component_data(lcsc_id)

    if download_type == "step" and step_data:
        buffer = BytesIO()
        buffer.write(step_data)
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{name}.step",
            mimetype="application/step"
        )

    elif download_type == "kicad_mod" and footprint:
        kicad_mod = ExporterFootprintKicad(footprint).output.export()
        return send_file(
            BytesIO(kicad_mod.encode("utf-8")),
            as_attachment=True,
            download_name=f"{name}.kicad_mod",
            mimetype="text/plain"
        )

    elif download_type == "kicad_sym" and symbol:
        kicad_sym = ExporterSymbolKicad(symbol).output.export()
        return send_file(
            BytesIO(kicad_sym.encode("utf-8")),
            as_attachment=True,
            download_name=f"{name}.kicad_sym",
            mimetype="text/plain"
        )

    else:
        abort(404)


@app.route("/")
def index():
    return """
    <title>LCSC KiCad Part Downloader</title>
    <h2>LCSC Component Downloader</h2>
    <form action="/get_model" method="GET">
        LCSC ID: <input type="text" name="lcsc_id"><br><br>
        Download type:
        <select name="type">
            <option value="step">3D STEP Model (.step)</option>
            <option value="kicad_mod">KiCad Footprint (.kicad_mod)</option>
            <option value="kicad_sym">KiCad Symbol (.kicad_sym)</option>
        </select><br><br>
        <input type="submit" value="Download">
    </form>
    """


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
