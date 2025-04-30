from flask import Flask, send_file, request, abort
from io import BytesIO
import tempfile
import os

from easyeda2kicad.easyeda.easyeda_api import EasyedaApi
from easyeda2kicad.easyeda.easyeda_importer import (
    EasyedaSymbolImporter,
    EasyedaFootprintImporter,
    Easyeda3dModelImporter,
)
from easyeda2kicad.kicad.export_kicad_symbol import ExporterSymbolKicad
from easyeda2kicad.kicad.export_kicad_footprint import ExporterFootprintKicad
from easyeda2kicad.kicad.parameters_kicad_symbol import KicadVersion

app = Flask(__name__)


def get_cad_data(lcsc_id: str):
    try:
        return EasyedaApi().get_cad_data_of_component(lcsc_id)
    except Exception:
        return None


@app.route("/get_symbol", methods=["GET"])
@app.route("/get_symbol/<lcsc_id>", methods=["GET"])
def get_symbol(lcsc_id=None):
    from easyeda2kicad.helpers import add_component_in_symbol_lib_file

    lcsc_id = lcsc_id or request.args.get("lcsc_id")
    if not lcsc_id:
        abort(400, "Missing LCSC ID")

    cad_data = get_cad_data(lcsc_id)
    if not cad_data:
        abort(404, "Component not found")

    symbol = EasyedaSymbolImporter(cad_data).get_symbol()
    exporter = ExporterSymbolKicad(symbol, KicadVersion.v6)
    lib_block = exporter.export(footprint_lib_name="easyeda2kicad")

    with tempfile.NamedTemporaryFile("w+", suffix=".kicad_sym", delete=False) as f:
        f.write("(kicad_symbol_lib (version 20211014) (generator easyeda2kicad)\n")
        f.write(lib_block)
        f.write(")\n")
        temp_path = f.name

    with open(temp_path, "rb") as f:
        content = f.read()
    os.remove(temp_path)

    buffer = BytesIO()
    buffer.write(content)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{lcsc_id}.kicad_sym",
        mimetype="text/plain",
    )


@app.route("/get_footprint", methods=["GET"])
@app.route("/get_footprint/<lcsc_id>", methods=["GET"])
def get_footprint(lcsc_id=None):
    lcsc_id = lcsc_id or request.args.get("lcsc_id")
    if not lcsc_id:
        abort(400, "Missing LCSC ID")

    cad_data = get_cad_data(lcsc_id)
    if not cad_data:
        abort(404, "Component not found")

    footprint = EasyedaFootprintImporter(cad_data).get_footprint()
    exported = ExporterFootprintKicad(footprint)

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = f"{footprint.info.name}.kicad_mod"
        filepath = os.path.join(tmpdir, filename)

        exported.export(
            footprint_full_path=filepath,
            model_3d_path="${KIPRJMOD}/3dmodels",
        )

        with open(filepath, "rb") as f:
            content = f.read()

    buffer = BytesIO()
    buffer.write(content)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="text/plain",
    )


@app.route("/get_step", methods=["GET"])
@app.route("/get_step/<lcsc_id>", methods=["GET"])
def get_step(lcsc_id=None):
    lcsc_id = lcsc_id or request.args.get("lcsc_id")
    if not lcsc_id:
        abort(400, "Missing LCSC ID")

    cad_data = get_cad_data(lcsc_id)
    if not cad_data:
        abort(404, "Component not found")

    model = Easyeda3dModelImporter(cad_data, download_raw_3d_model=False).create_3d_model()
    if not model or not model.step:
        abort(404, "STEP model not available")

    buffer = BytesIO()
    buffer.write(model.step)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{model.name}.step",
        mimetype="application/step",
    )


@app.route("/")
def index():
    return """
    <title>LCSC KiCad Exporter</title>
    <h2>Download KiCad Symbol, Footprint, or STEP</h2>
    <form method="get">
        <label>LCSC ID: <input name="lcsc_id" type="text" required></label><br><br>
        <button formaction="/get_symbol">Download Symbol (.kicad_sym)</button><br><br>
        <button formaction="/get_footprint">Download Footprint (.kicad_mod)</button><br><br>
        <button formaction="/get_step">Download 3D Model (.step)</button>
    </form>
    """


if __name__ == '__main__':
    app.run()
