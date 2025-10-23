import os
from flask import Flask, jsonify, request

try:
    import ibm_db
    HAS_IBM_DB = True
except Exception:
    HAS_IBM_DB = False


def create_app():
    app = Flask(__name__)

    @app.route('/ping')
    def ping():
        return jsonify({'status': 'pong'})

    @app.route('/query', methods=['POST'])
    def query():
        # data = request.get_json() or {}
        # sql = data.get('sql')
        sql = 'SELECT * FROM DB2INST1.USERS'
        if not sql:
            return jsonify({'error': 'missing sql'}), 400

        # Demo safety: only allow simple SELECT queries
        if not sql.strip().lower().startswith('select'):
            return jsonify({'error': 'only SELECT allowed in this demo'}), 400

        if not HAS_IBM_DB:
            return jsonify({'error': 'ibm_db not installed in environment'}), 503

        conn_str = _build_conn_str_from_env()
        if not conn_str:
            return jsonify({'error': 'db credentials not configured'}), 400

        
        try:
            conn = ibm_db.connect(conn_str, '', '')
            stmt = ibm_db.exec_immediate(conn, sql)
            rows = []
            row = ibm_db.fetch_assoc(stmt)
            while row:
                rows.append(row)
                row = ibm_db.fetch_assoc(stmt)
            ibm_db.close(conn)
            return jsonify({'rows': rows})
        except Exception as e:
            return jsonify({'error:::': str(e)}), 500

    return app


def _build_conn_str_from_env():
    host = os.getenv('DB_HOST')
    port = os.getenv('DB_PORT')
    db = os.getenv('DB_NAME')
    user = os.getenv('DB_USER')
    pwd = os.getenv('DB_PASSWORD')
    if not all([host, port, db, user, pwd]):
        return None
    return f"DATABASE={db};HOSTNAME={host};PORT={port};PROTOCOL=TCPIP;UID={user};PWD={pwd};"


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')))
