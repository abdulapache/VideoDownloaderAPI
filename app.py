from flask import Flask, request
from flask_restx import Api, Resource, fields
import yt_dlp
import os
import shutil
import socket

# Flask App and Swagger API Setup
app = Flask(__name__)
api = Api(app, version='1.0', title='Video Downloader API',
          description='Download videos from YouTube, Facebook, Instagram etc. using yt-dlp',
          doc='/swagger')  # Swagger UI available at /swagger

ns = api.namespace('api', description='Download operations')

# Define expected input model
download_model = api.model('DownloadRequest', {
    'url': fields.String(required=True, description='Video URL to download')
})

# API Endpoint
@ns.route('/download')
class VideoDownloader(Resource):
    @ns.expect(download_model)
    def post(self):
        """Download video from a given URL"""
        try:
            url = request.json.get('url')
            if not url:
                return {'success': False, 'message': 'No URL provided'}, 400

            if not shutil.which("ffmpeg"):
                return {'success': False, 'message': 'ffmpeg not found in PATH'}, 500

            os.makedirs('downloads', exist_ok=True)

            ydl_opts = {
                'outtmpl': 'downloads/%(title).50s.%(ext)s',
                'restrictfilenames': True,
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'socket_timeout': 30,
                'quiet': True,
                'prefer_ffmpeg': True,
                'addmetadata': True,
                'cookiefile': 'cookies.txt',
                'postprocessors': [
                    {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},
                    {'key': 'FFmpegMetadata'},
                    {'key': 'FFmpegEmbedSubtitle'}
                ],
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                }
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            return {'success': True, 'message': '✅ Download completed successfully.'}

        except socket.timeout:
            return {'success': False, 'message': '⏱️ Download timed out. Try again.'}, 500
        except yt_dlp.utils.DownloadError as e:
            return {'success': False, 'message': f'⚠️ yt-dlp error: {str(e)}'}, 500
        except Exception as e:
            return {'success': False, 'message': f'❌ Error: {str(e)}'}, 500

# Start Flask App
if __name__ == '__main__':
    app.run(debug=True)
