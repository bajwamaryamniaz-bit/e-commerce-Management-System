import os
import sys
import socket
import threading

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.app import create_app

def start_ipv6_bridge(port):
    """
    On Windows 10/11, 'localhost' often resolves to IPv6 '::1'.
    This bridge ensures that both http://localhost:PORT and http://127.0.0.1:PORT
    work seamlessly without connection refused errors.
    """
    try:
        ipv6_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        ipv6_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ipv6_sock.bind(('::1', port))
        ipv6_sock.listen(10)
        
        while True:
            client, _ = ipv6_sock.accept()
            def handle_client(c):
                try:
                    target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    target.connect(('127.0.0.1', port))
                    
                    def forward(src, dst):
                        try:
                            while True:
                                data = src.recv(8192)
                                if not data:
                                    break
                                dst.sendall(data)
                        except Exception:
                            pass
                        finally:
                            try: src.close()
                            except: pass
                            try: dst.close()
                            except: pass

                    t1 = threading.Thread(target=forward, args=(c, target), daemon=True)
                    t2 = threading.Thread(target=forward, args=(target, c), daemon=True)
                    t1.start()
                    t2.start()
                except Exception:
                    try: c.close()
                    except: pass

            threading.Thread(target=handle_client, args=(client,), daemon=True).start()
    except Exception:
        # If port is already bound or IPv6 disabled, continue without error
        pass

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    
    # Start dual-stack bridge for localhost (::1) support
    threading.Thread(target=start_ipv6_bridge, args=(port,), daemon=True).start()

    print("\n" + "="*60)
    print("  🚀 E-COMMERCE MANAGEMENT SYSTEM (DBMS PROJECT)")
    print(f"  🌐 Localhost URL   : http://localhost:{port}")
    print(f"  🌐 Direct IPv4 URL : http://127.0.0.1:{port}")
    print(f"  🤖 AI Assistant    : Active (Widget & /ai-assistant.html)")
    print(f"  📊 API Status      : Ready & Parameterized SQL Active")
    print("="*60 + "\n")

    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
