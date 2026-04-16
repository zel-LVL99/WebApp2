import http.server
import json
import random
import socketserver
import urllib.parse
import os

PORT = 8000
cart_state = {
    "hygiene": 0,
    "powerbank": 0,
    "solar": 0,
}

class LiveCountHandler(http.server.SimpleHTTPRequestHandler):
    def _send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/count":
            count = random.randint(25, 70)
            self._send_json({"count": count})
            return

        if parsed.path == "/cart":
            params = urllib.parse.parse_qs(parsed.query)
            action = params.get("action", [""])[0]
            item = params.get("item", [""])[0]
            if item in cart_state and action in {"add", "subtract"}:
                if action == "add":
                    cart_state[item] += 1
                elif action == "subtract" and cart_state[item] > 0:
                    cart_state[item] -= 1
            item_prices = {
                "hygiene": 9.99,
                "powerbank": 19.99,
                "solar": 29.99,
            }
            item_count = sum(cart_state.values())
            subtotal = sum(cart_state[key] * item_prices[key] for key in cart_state)
            delivery_fee = 4.99 if item_count > 0 else 0.0
            total_amount = round(subtotal + delivery_fee, 2)
            self._send_json({
                "cart": cart_state,
                "subtotal": round(subtotal, 2),
                "deliveryFee": round(delivery_fee, 2),
                "totalAmount": total_amount,
                "totalItems": item_count,
            })
            return

        if parsed.path == "/calculate":
            params = urllib.parse.parse_qs(parsed.query)
            item = params.get("item", [""])[0]
            qty = int(params.get("qty", ["1"])[0] or 1)
            item_prices = {
                "hygiene": 9.99,
                "powerbank": 19.99,
                "solar": 29.99,
            }
            if item in item_prices and qty >= 1:
                unit_price = item_prices[item]
                total = round(unit_price * qty, 2)
                self._send_json({
                    "item": item,
                    "qty": qty,
                    "unitPrice": unit_price,
                    "total": total,
                })
                return
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid item or quantity."}).encode("utf-8"))
            return

        return super().do_GET()

if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__) or ".")
    with socketserver.TCPServer(("", PORT), LiveCountHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")