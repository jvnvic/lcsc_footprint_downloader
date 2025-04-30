@app.route("/")
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>LCSC KiCad Exporter</title>
        <style>
            body {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }

            h2 {
                color: #ffa500;
                margin-bottom: 1rem;
            }

            form {
                background-color: #1e1e1e;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 0 12px rgba(0, 0, 0, 0.5);
                max-width: 400px;
                width: 100%;
                text-align: center;
            }

            label {
                display: block;
                margin-bottom: 1rem;
                font-size: 1rem;
            }

            input[type="text"] {
                padding: 0.5rem;
                width: 100%;
                border: 1px solid #333;
                border-radius: 8px;
                background-color: #2c2c2c;
                color: #fff;
                font-size: 1rem;
                margin-top: 0.5rem;
            }

            button {
                margin-top: 1rem;
                background-color: #ffa500;
                border: none;
                color: #121212;
                font-weight: bold;
                padding: 0.7rem 1.2rem;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1rem;
                width: 100%;
                transition: background-color 0.2s ease;
            }

            button:hover {
                background-color: #ff8800;
            }

            button + button {
                margin-top: 0.5rem;
            }
        </style>
    </head>
    <body>
        <h2>LCSC KiCad Exporter</h2>
        <form method="get">
            <label>
                LCSC ID:
                <input name="lcsc_id" type="text" placeholder="e.g., C2040" required />
            </label>
            <button formaction="/get_symbol">Download Symbol (.kicad_sym)</button>
            <button formaction="/get_footprint">Download Footprint (.kicad_mod)</button>
            <button formaction="/get_step">Download 3D Model (.step)</button>
            <button formaction="/get_all">Download All as ZIP</button>
        </form>
    </body>
    </html>
    """
