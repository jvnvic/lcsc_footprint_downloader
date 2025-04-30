from flask import Flask, send_file, request, abort
from io import BytesIO
import tempfile
import os
import zipfile

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

    try:
        api = EasyedaApi()
        cad_data = api.get_cad_data_of_component(lcsc_id)
        model = Easyeda3dModelImporter(cad_data, download_raw_3d_model=False).create_3d_model()

        if not model or not model.uuid:
            abort(404, "Model UUID missing")

        step_data = api.get_step_3d_model(model.uuid)
        if not step_data:
            abort(404, "STEP data not found")

        buffer = BytesIO()
        buffer.write(step_data)
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{model.name}.step",
            mimetype="application/step",
        )
    except Exception as e:
        print("STEP download error:", e)
        abort(500, "Internal error fetching STEP model")


@app.route("/get_all", methods=["GET"])
@app.route("/get_all/<lcsc_id>", methods=["GET"])
def get_all(lcsc_id=None):
    lcsc_id = lcsc_id or request.args.get("lcsc_id")
    if not lcsc_id:
        abort(400, "Missing LCSC ID")

    cad_data = get_cad_data(lcsc_id)
    if not cad_data:
        abort(404, "Component not found")

    files = {}

    # SYMBOL
    symbol = EasyedaSymbolImporter(cad_data).get_symbol()
    symbol_exporter = ExporterSymbolKicad(symbol, KicadVersion.v6)
    symbol_str = (
        "(kicad_symbol_lib (version 20211014) (generator easyeda2kicad)\n"
        + symbol_exporter.export(footprint_lib_name="easyeda2kicad")
        + ")\n"
    )
    files[f"{lcsc_id}.kicad_sym"] = symbol_str.encode("utf-8")

    # FOOTPRINT
    footprint = EasyedaFootprintImporter(cad_data).get_footprint()
    footprint_exporter = ExporterFootprintKicad(footprint)
    with tempfile.TemporaryDirectory() as tmpdir:
        fp_path = os.path.join(tmpdir, f"{footprint.info.name}.kicad_mod")
        footprint_exporter.export(fp_path, model_3d_path="${KIPRJMOD}/3dmodels")
        with open(fp_path, "rb") as f:
            files[f"{footprint.info.name}.kicad_mod"] = f.read()

    # STEP
    try:
        api = EasyedaApi()
        model = Easyeda3dModelImporter(cad_data, download_raw_3d_model=False).create_3d_model()
        if model and model.uuid:
            step_data = api.get_step_3d_model(model.uuid)
            if step_data:
                files[f"{model.name}.step"] = step_data
    except Exception as e:
        print(f"STEP error: {e}")

    # ZIP all
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for filename, data in files.items():
            zipf.writestr(filename, data)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"{lcsc_id}.zip",
        mimetype="application/zip",
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
        <button formaction="/get_step">Download 3D Model (.step)</button><br><br>
        <button formaction="/get_all">Download All as ZIP</button>
    </form>
    """


if __name__ == '__main__':
    app.run()
