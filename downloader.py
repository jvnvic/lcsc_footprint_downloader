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
        api = EasyedaApi()
        return api.get_cad_data_of_component(lcsc_id)
    except Exception:
        return None


@app.route("/get_symbol/<lcsc_id>")
def get_symbol(lcsc_id):
    cad_data = get_cad_data(lcsc_id)
    if not cad_data:
        abort(404)

    symbol = EasyedaSymbolImporter(cad_data).get_symbol()
    exported = ExporterSymbolKicad(symbol, KicadVersion.v6)
    ki_symbol_str = exported.output.export_v6()

    buffer = BytesIO()
    buffer.write("\n".join(ki_symbol_str).encode("utf-8"))
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{lcsc_id}.kicad_sym",
        mimetype="text/plain",
    )


@app.route("/get_footprint/<lcsc_id>")
def get_footprint(lcsc_id):
    cad_data = get_cad_data(lcsc_id)
    if not cad_data:
        abort(404)

    footprint = EasyedaFootprintImporter(cad_data).get_footprint()
    exported = ExporterFootprintKicad(footprint)
    ki_fp = exported.get_ki_footprint()

    # Reuse export logic to write .kicad_mod into buffer
    buffer = BytesIO()
    ki_lib = exported.export(footprint_full_path="", model_3d_path="")  # get string
    buffer.write(ki_lib.encode("utf-8"))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{lcsc_id}.kicad_mod",
        mimetype="text/plain",
    )


@app.route("/get_step/<lcsc_id>")
def get_step(lcsc_id):
    cad_data = get_cad_data(lcsc_id)
    if not cad_data:
        abort(404)

    model = Easyeda3dModelImporter(cad_data, download_raw_3d_model=False).create_3d_model()
    if not model or not model.step:
        abort(404)

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
        LCSC ID: <input name="lcsc_id" type="text">
        <button formaction="/get_symbol/" type="submit">Symbol</button>
        <button formaction="/get_footprint/" type="submit">Footprint</button>
        <button formaction="/get_step/" type="submit">STEP Model</button>
    </form>
    """


if __name__ == '__main__':
    app.run()
