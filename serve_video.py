from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

os.chdir('/root/setup/video-api/storage/')
httpd = HTTPServer(('0.0.0.0', 8081), SimpleHTTPRequestHandler)
print("Servidor corriendo en puerto 8081")
httpd.serve_forever()
