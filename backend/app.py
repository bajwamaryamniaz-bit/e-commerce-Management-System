import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from .config import Config

def create_app():
    # Robust resolution of frontend directory across local and cloud environments
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.abspath(os.path.join(base_dir, '..', 'frontend')),
        os.path.abspath(os.path.join(base_dir, '..', 'api', 'frontend')),
        os.path.abspath(os.path.join(os.getcwd(), 'frontend')),
        os.path.abspath(os.path.join(base_dir, 'frontend')),
        '/var/task/frontend',
        '/var/task/api/frontend'
    ]
    frontend_dir = candidates[0]
    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            frontend_dir = c
            break

    app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
    app.config.from_object(Config)

    # Enable CORS for local cross-origin development
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register API Blueprints
    from .routes.auth import auth_bp
    from .routes.products import products_bp
    from .routes.customers import customers_bp
    from .routes.suppliers import suppliers_bp
    from .routes.purchases import purchases_bp
    from .routes.sales import sales_bp
    from .routes.inventory import inventory_bp
    from .routes.reports import reports_bp
    from .routes.ai import ai_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(customers_bp, url_prefix='/api/customers')
    app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
    app.register_blueprint(purchases_bp, url_prefix='/api/purchases')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')

    # Frontend serving routes
    @app.route('/')
    def serve_dashboard():
        if os.path.exists(os.path.join(frontend_dir, 'login.html')):
            return send_from_directory(frontend_dir, 'login.html')
        for cand in candidates:
            if os.path.exists(os.path.join(cand, 'login.html')):
                return send_from_directory(cand, 'login.html')
        return "<h3>E-Commerce Management System API is running!</h3><p>Frontend assets are loading.</p>", 200

    @app.route('/<path:path>')
    def serve_static(path):
        if os.path.exists(os.path.join(frontend_dir, path)):
            return send_from_directory(frontend_dir, path)
        for cand in candidates:
            if os.path.exists(os.path.join(cand, path)):
                return send_from_directory(cand, path)
        if os.path.exists(os.path.join(frontend_dir, 'index.html')):
            return send_from_directory(frontend_dir, 'index.html')
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "message": "Internal server error"}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==================================================")
    print(f"🚀 E-Commerce DBMS Backend running on: http://localhost:{port}")
    print(f"📁 Serving Frontend from: {os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))}")
    print(f"==================================================\n")
    app.run(host='0.0.0.0', port=port, debug=True)
