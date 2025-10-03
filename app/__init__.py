import os
from flask import Flask
import socket

def create_app():
    """
    Factory function que crea y configura la aplicación Flask.
    """
    # Configurar rutas de plantillas y archivos estáticos
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Configuración básica
    app.config['SECRET_KEY'] = 'dev'  # Cambiar en producción
    
    # Configuración de rutas de archivos
    base_dir = os.path.dirname(os.path.dirname(__file__))
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'multimedia')
    app.config['ORIGINAL_FOLDER'] = os.path.join(base_dir, 'multimedia', 'originales')
    app.config['TRANSCODED_FOLDER'] = os.path.join(base_dir, 'multimedia', 'transcodificados')
    app.config['TEMP_FOLDER'] = os.path.join(base_dir, 'multimedia', 'temp')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 * 1024  # 10GB max upload size
    
    # Asegurar que los directorios existan
    os.makedirs(app.config['ORIGINAL_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TRANSCODED_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMP_FOLDER'], exist_ok=True)
    
    # Configuración del servidor RTMP para HLS
    # Obtener automáticamente la IP de la máquina
    def get_local_ip():
        try:
            # Intentar conectar a una dirección IP externa para determinar la IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.1)
            s.connect(('8.8.8.8', 80))  # Usar el DNS de Google
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"No se pudo determinar la IP local: {e}")
            try:
                # Si falla, intentar con el nombre de host
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                if local_ip.startswith('127.'):
                    return '127.0.0.1'
                return local_ip
            except:
                return '127.0.0.1'
    
    # Usar la IP local detectada automáticamente para el servidor RTMP
    RTMP_SERVER_IP = get_local_ip()
    app.config['RTMP_SERVER'] = RTMP_SERVER_IP
    print(f"Servidor RTMP configurado en: rtmp://{RTMP_SERVER_IP}:1935")
    print(f"Si necesitas acceder desde otra red, asegúrate de que el puerto 1935 esté abierto en el firewall")
    
    # Registrar blueprints
    from .routes import main_bp
    from .api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Inicializar el procesador de video
    from .video_processor import video_processor
    video_processor.start_workers()
    
    # Configurar limpieza al cerrar la aplicación
    import atexit
    atexit.register(video_processor.stop_workers)
    
    return app
