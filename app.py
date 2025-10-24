import os
from flask import Flask, jsonify, request

try:
    import ibm_db
    HAS_IBM_DB = True
except Exception:
    HAS_IBM_DB = False

try:
    from sqlalchemy import create_engine, text
    HAS_SQLALCHEMY = True
except Exception:
    HAS_SQLALCHEMY = False


def create_app():
    app = Flask(__name__)

    @app.route('/ping')
    def ping():
        return jsonify({'status': 'pong'})

    @app.route('/query', methods=['POST'])
    def query():
        sql = "SELECT * FROM USERS;"
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
            return jsonify({'error': str(e)}), 500        
        # End of /query route

    @app.route('/get_users', methods=['GET'])
    def get_users():
        """Return all rows from USERS using SQLAlchemy (ibm_db_sa dialect).

        Falls back to 503 if SQLAlchemy or the dialect is not installed, or 400 if
        DB credentials are missing.
        """
        if not HAS_SQLALCHEMY:
            return jsonify({'error': 'SQLAlchemy or ibm_db_sa not installed'}), 503

        host = os.getenv('DB_HOST')
        port = os.getenv('DB_PORT')
        db = os.getenv('DB_NAME')
        user = os.getenv('DB_USER')
        pwd = os.getenv('DB_PASSWORD')
        if not all([host, port, db, user, pwd]):
            return jsonify({'error': 'db credentials not configured'}), 400

        # ibm_db_sa connection url: ibm_db_sa://user:pwd@host:port/dbname
        conn_url = f"ibm_db_sa://{user}:{pwd}@{host}:{port}/{db}"
        try:
            engine = create_engine(conn_url)
            with engine.connect() as conn:
                result = conn.execute(text('SELECT ID, NAME, EMAIL FROM USERS'))
                rows = []
                for row in result:
                    # SQLAlchemy Row supports _mapping in modern versions
                    if hasattr(row, '_mapping'):
                        rows.append(dict(row._mapping))
                    else:
                        rows.append(dict(zip(result.keys(), row)))
            return jsonify({'rows': rows})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


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
