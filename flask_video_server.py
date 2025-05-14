from flask import Flask, send_from_directory, send_file, Response
import os

app = Flask(__name__)

@app.route('/video/<path:filename>')
def serve_video(filename):
    video_path = os.path.join('/root/setup/video-api/storage/', filename)
    if not os.path.exists(video_path):
        return "Archivo no encontrado", 404
    
    return send_file(
        video_path,
        mimetype='video/mp4',
        as_attachment=False,
        download_name=os.path.basename(filename)
    )

@app.route('/test')
def test_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Test</title>
    </head>
    <body>
        <h1>Video Test</h1>
        <video width="640" height="360" controls>
            <source src="/video/2025/05/14/963a03e9-37ad-496f-9359-b2ee262fec0e.mp4" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
