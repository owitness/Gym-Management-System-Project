from flask import Blueprint, request, jsonify
from db import get_db
from middleware import authenticate, member_required
import logging
from middleware import admin_required  # Make sure this is imported

logger = logging.getLogger(__name__)

equipment_bp = Blueprint('equipment', __name__)

@equipment_bp.route('/report', methods=['POST'])
@authenticate
@member_required
def report_equipment_issue(user):
    logger.debug(f"DEBUG: report_equipment_issue called with user: {user}")  # Add logging
    data = request.get_json()
    logger.debug(f"DEBUG: Request JSON data: {data}")  # Add logging
    equipment_name = data.get('equipment_name')
    issue_description = data.get('issue_description')

    if not equipment_name or not issue_description:
        return jsonify({'error': 'Equipment name and issue description are required'}), 400

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO equipment_reports (user_id, equipment_name, issue_description)
                VALUES (%s, %s, %s)
            """, (user['id'], equipment_name, issue_description))
            conn.commit()
            return jsonify({'message': 'Issue reported successfully'}), 201
    except Exception as e:
        logger.error(f"DEBUG: Database error: {str(e)}")  # Add logging
        return jsonify({'error': 'Failed to save report'}), 500
    


@equipment_bp.route('/reports', methods=['GET'])
@authenticate
@admin_required
def get_equipment_reports(user):
    try:
        with get_db() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT 
                    er.id, 
                    u.name AS reported_by, 
                    er.equipment_name, 
                    er.issue_description, 
                    er.reported_at
                FROM equipment_reports er
                JOIN users u ON er.user_id = u.id
                ORDER BY er.reported_at DESC
            """)
            reports = cursor.fetchall()
            return jsonify(reports)
    except Exception as e:
        logger.error(f"Error fetching equipment reports: {str(e)}")
        return jsonify({'error': 'Failed to fetch reports'}), 500

