from flask import Blueprint, jsonify, current_app
import os
from .video_processor import video_processor

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/transcoding/status/<filename>')
def get_transcoding_status(filename):
    """Obtiene el estado de transcodificación de un archivo.
    
    Args:
        filename: Nombre del archivo a verificar
        
    Returns:
        JSON con el estado de transcodificación
    """
    # Verificar si el archivo existe en la carpeta de originales
    original_path = os.path.join(current_app.config['ORIGINAL_FOLDER'], filename)
    if not os.path.exists(original_path):
        return jsonify({
            'success': False,
            'error': 'Archivo no encontrado',
            'filename': filename
        }), 404
    
    # Verificar si hay una tarea de transcodificación en curso
    task_info = None
    for task_id, task in video_processor.active_tasks.items():
        if task.get('filename') == filename:
            task_info = {
                'task_id': task_id,
                'status': 'processing',
                'progress': task.get('progress', 0),
                'started_at': task.get('started_at'),
                'filename': filename
            }
            break
    
    # Si no hay tarea en curso, verificar si existe la versión transcodificada
    if not task_info:
        name, ext = os.path.splitext(filename)
        transcoded_path = os.path.join(current_app.config['TRANSCODED_FOLDER'], f"{name}.mp4")
        
        if os.path.exists(transcoded_path):
            return jsonify({
                'success': True,
                'status': 'completed',
                'filename': filename,
                'transcoded_path': transcoded_path,
                'size': os.path.getsize(transcoded_path)
            })
        else:
            return jsonify({
                'success': True,
                'status': 'pending',
                'filename': filename,
                'message': 'No hay tarea de transcodificación en curso para este archivo'
            })
    
    return jsonify({
        'success': True,
        **task_info
    })
