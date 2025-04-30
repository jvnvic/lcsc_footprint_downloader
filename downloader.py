@app.route("/get_symbol", methods=["GET"])
@app.route("/get_symbol/<lcsc_id>", methods=["GET"])
def get_symbol(lcsc_id=None):
    import tempfile
    from easyeda2kicad.helpers import add_component_in_symbol_lib_file

    lcsc_id = lcsc_id or request.args.get("lcsc_id")
    if not lcsc_id:
        abort(400, "Missing LCSC ID")

    cad_data = get_cad_data(lcsc_id)
    if not cad_data:
        abort(404, "Component not found")

    # Import and export symbol
    symbol = EasyedaSymbolImporter(cad_data).get_symbol()
    exporter = ExporterSymbolKicad(symbol, KicadVersion.v6)
    lib_block = exporter.export(footprint_lib_name="easyeda2kicad")

    # Write into a temporary full library file
    with tempfile.NamedTemporaryFile("w+", suffix=".kicad_sym", delete=False) as f:
        f.write(
            "(kicad_symbol_lib (version 20211014) (generator easyeda2kicad)\n"
        )
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
