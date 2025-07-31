from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp
import os
import shutil

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = os.path.join(os.getcwd(), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/api/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url')
        format_type = data.get('format', 'mp4')

        if not url:
            return jsonify({'success': False, 'message': '❌ No URL provided'}), 400

        if not shutil.which("ffmpeg"):
            return jsonify({'success': False, 'message': '❌ ffmpeg not found in PATH'}), 500

        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(title).50s.%(ext)s',
            'restrictfilenames': True,
            'quiet': True,
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'prefer_ffmpeg': True,
            'postprocessors': [],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0'
            }
        }

        # Handle format
        if format_type == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif format_type == 'hd':
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif format_type == '4k':
            ydl_opts['format'] = 'bestvideo[height>=2160]+bestaudio/best[height>=2160]'
        else:  # default mp4
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
            ydl_opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if format_type == 'mp3':
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
            file_name = os.path.basename(file_path)

        return jsonify({
            'success': True,
            'message': '✅ Download complete!',
            'file_url': f'http://localhost:5000/downloaded/{file_name}'
        })

    except yt_dlp.utils.DownloadError as e:
        return jsonify({'success': False, 'message': f'⚠️ yt-dlp error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'❌ Error: {str(e)}'}), 500

@app.route('/downloaded/<path:filename>', methods=['GET'])
def serve_file(filename):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
