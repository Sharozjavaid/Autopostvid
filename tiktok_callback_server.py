#!/usr/bin/env python3
"""
Simple callback server to capture TikTok OAuth code.
Run this on port 8501 to receive the redirect.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        
        code = params.get('code', [None])[0]
        state = params.get('state', [None])[0]
        error = params.get('error', [None])[0]
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        if code:
            html = f"""
            <html>
            <head><title>TikTok Auth Success!</title></head>
            <body style="font-family: Arial; padding: 40px; background: #1a1a2e; color: #eee;">
                <h1 style="color: #00f5d4;">✅ Authorization Successful!</h1>
                <p>Your authorization code:</p>
                <pre style="background: #16213e; padding: 20px; border-radius: 8px; 
                           font-size: 14px; word-break: break-all; color: #00f5d4;">
{code}
                </pre>
                <p style="margin-top: 20px;">Now run this command:</p>
                <pre style="background: #16213e; padding: 20px; border-radius: 8px; color: #ffd700;">
python3 tiktok_cli.py token --code "{code}"
                </pre>
                <p style="color: #888; margin-top: 30px;">State: {state}</p>
            </body>
            </html>
            """
            print(f"\n{'='*60}")
            print("✅ GOT AUTHORIZATION CODE!")
            print(f"{'='*60}")
            print(f"\nCode: {code}")
            print(f"\nRun: python3 tiktok_cli.py token --code \"{code}\"")
            print(f"{'='*60}\n")
        elif error:
            html = f"""
            <html>
            <head><title>TikTok Auth Error</title></head>
            <body style="font-family: Arial; padding: 40px; background: #1a1a2e; color: #eee;">
                <h1 style="color: #ff6b6b;">❌ Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>{params.get('error_description', [''])[0]}</p>
            </body>
            </html>
            """
            print(f"\n❌ Auth Error: {error}")
        else:
            html = """
            <html>
            <head><title>TikTok Callback</title></head>
            <body style="font-family: Arial; padding: 40px; background: #1a1a2e; color: #eee;">
                <h1>TikTok OAuth Callback Server</h1>
                <p>Waiting for authorization redirect...</p>
            </body>
            </html>
            """
        
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8501
    
    print(f"\n{'='*60}")
    print("🌐 TikTok OAuth Callback Server")
    print(f"{'='*60}")
    print(f"Listening on http://localhost:{port}")
    print("Waiting for TikTok redirect...")
    print(f"{'='*60}\n")
    
    server = HTTPServer(('', port), CallbackHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
