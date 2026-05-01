from flask import Flask, Response, render_template_string
import requests
import io
from PyPDF2 import PdfMerger
import time
import os

app = Flask(__name__)

# 🔐 Token (direct hardcoded — jaise tu bola)
FIXED_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY5NWI0MmJjNzQwZGFkMjQzN2I1NzhlYiIsInJvbGUiOiJzdHVkZW50IiwiaXAiOiIxNTIuNTkuMTguMTM4IiwiZGV2aWNlIjoiTW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzE0NS4wLjAuMCBTYWZhcmkvNTM3LjM2IiwiaWF0IjoxNzcyMjY2NTU3LCJleHAiOjE4MzUzMzg1NTd9.vBUp5SWekeBxGy-oIqslR2IRzTpfXxcUqcojVyr5boM"

HEADERS = {
    'user-agent': 'Mozilla/5.0',
    'origin': 'https://ebooks.ssccglpinnacle.com',
    'referer': 'https://ebooks.ssccglpinnacle.com/'
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pinnacle Downloader</title>
</head>
<body style="text-align:center; margin-top:50px;">
    <h2>📚 Pinnacle Book Downloader</h2>
    <input type="text" id="bid" placeholder="Enter Book ID">
    <br><br>
    <button onclick="dl()">Download PDF</button>

    <script>
        function dl() {
            var id = document.getElementById('bid').value;
            if(!id) return alert("ID daal!");
            window.location.href = "/fullbook/" + id;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route('/fullbook/<book_id>')
def full_book(book_id):
    auth_headers = {**HEADERS, 'authorization': f'Bearer {FIXED_TOKEN}'}

    try:
        chapters_url = f"https://auth.ssccglpinnacle.com/api/chapters-ebook/{book_id}"
        r = requests.get(chapters_url, headers=auth_headers, timeout=10)
        r.raise_for_status()
        chapters = r.json()

        if not chapters:
            return "❌ No chapters found", 404

        merger = PdfMerger()
        success_count = 0

        # ⚠️ Safe limit (Render free)
        for chap in chapters[:50]:
            c_id = chap.get('_id')
            if not c_id:
                continue

            try:
                res = requests.get(
                    f'https://auth.ssccglpinnacle.com/api/content-ebook/{c_id}',
                    headers=auth_headers,
                    timeout=5
                )

                if res.status_code == 200:
                    merger.append(io.BytesIO(res.content))
                    success_count += 1

            except Exception:
                continue

            time.sleep(0.05)

        if success_count == 0:
            return "❌ No pages downloaded", 500

        output = io.BytesIO()
        merger.write(output)
        output.seek(0)

        return Response(
            output.read(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename=Book_{book_id[-5:]}.pdf'
            }
        )

    except requests.exceptions.Timeout:
        return "⚠️ Timeout! Book badi hai. Try again.", 504
    except Exception as e:
        return f"❌ Error: {str(e)}", 500


# ✅ Render ke liye run
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
