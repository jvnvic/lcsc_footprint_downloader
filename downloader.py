from flask import Flask, send_file, request, abort
from io import BytesIO

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
    lcsc_id = lcsc_id or request.args.get("lcsc_id")
    if not lcsc_id:
        abort(400, "Missing LCSC ID")

    cad_data = get_cad_data(lcsc_id)
    if not cad_data:
        abort(404, "Component not found")

    symbol = EasyedaSymbolImporter(cad_data).get_symbol()
    exported = ExporterSymbolKicad(symbol, KicadVersion.v6)

    ki_symbol_body = exported.output.export_v6()
    ki_symbol_str = f"""(kicad_symbol_lib (version 20211014) (generator easyeda2kicad)
{ki_symbol_body}
)"""

    buffer = BytesIO()
    buffer.write(ki_symbol_str.encode("utf-8"))
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
    ki = exported.get_ki_footprint()

    mod_str = f"(module {ki.info.name} (layer F.Cu) (tedit 5DC5F6A4)\n"
    mod_str += "  (fp_text reference REF** (at 0 0) (layer F.SilkS)\n    (effects (font (size 1 1) (thickness 0.15)))\n  )\n"
    mod_str += f"  (fp_text value {ki.info.name} (at 0 0) (layer F.Fab)\n    (effects (font (size 1 1) (thickness 0.15)))\n  )\n"

    for pad in ki.pads:
        drill = f" {pad.drill}" if pad.drill else ""
        mod_str += f"  (pad {pad.number} {pad.type} {pad.shape} (at {pad.pos_x:.2f} {pad.pos_y:.2f} {pad.orientation:.2f}) " \
                   f"(size {pad.width:.2f} {pad.height:.2f}) (layers {pad.layers}){drill})\n"

    mod_str += ")\n"

    buffer = BytesIO()
    buffer.write(mod_str.encode("utf-8"))
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{lcsc_id}.kicad_mod",
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
