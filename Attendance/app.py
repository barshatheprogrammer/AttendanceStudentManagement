from flask import Flask, jsonify, request, send_file, render_template
from flask_cors import CORS
import mysql.connector
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io, base64

app = Flask(__name__)
CORS(app)

# Serve home page
@app.route('/')
def home():
    return render_template('index.html')

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change to your MySQL username
    'password': 'bca3rd30901222131',  # Change to your MySQL password
    'database': 'attendance_system'
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# Merge Sort implementation for sorting
def merge_sort(arr, key, reverse=False):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key, reverse)
    right = merge_sort(arr[mid:], key, reverse)
    
    return merge(left, right, key, reverse)

def merge(left, right, key, reverse):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if reverse:
            if left[i][key] > right[j][key]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        else:
            if left[i][key] < right[j][key]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# Binary Search implementation for searching
def binary_search(arr, key, value):
    arr = merge_sort(arr, key)
    left, right = 0, len(arr) - 1
    results = []
    
    while left <= right:
        mid = (left + right) // 2
        if str(arr[mid][key]).lower().find(value.lower()) != -1:
            results.append(arr[mid])
            # Check adjacent elements
            i = mid - 1
            while i >= 0 and str(arr[i][key]).lower().find(value.lower()) != -1:
                results.append(arr[i])
                i -= 1
            i = mid + 1
            while i < len(arr) and str(arr[i][key]).lower().find(value.lower()) != -1:
                results.append(arr[i])
                i += 1
            break
        elif str(arr[mid][key]).lower() < value.lower():
            left = mid + 1
        else:
            right = mid - 1
    
    return results

@app.route('/api/students', methods=['GET'])
def get_students():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get query parameters
        search = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'name')
        order = request.args.get('order', 'asc')
        
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        
        # Convert datetime objects to strings
        for student in students:
            if 'created_at' in student:
                student['created_at'] = str(student['created_at'])
        
        # Apply search using linear search for partial matches
        if search:
            students = [s for s in students if 
                       search.lower() in s['name'].lower() or 
                       search.lower() in s['roll_number'].lower() or
                       search.lower() in s['class'].lower()]
        
        # Apply sorting using merge sort
        if sort_by in ['name', 'roll_number', 'class']:
            students = merge_sort(students, sort_by, reverse=(order == 'desc'))
        
        cursor.close()
        conn.close()
        
        return jsonify(students)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/students', methods=['POST'])
def add_student():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO students (name, roll_number, class, email) VALUES (%s, %s, %s, %s)",
            (data['name'], data['roll_number'], data['class'], data['email'])
        )
        
        conn.commit()
        student_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Student added successfully', 'student_id': student_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        cursor.execute("""
            SELECT a.*, s.name, s.roll_number, s.class 
            FROM attendance a
            JOIN students s ON a.student_id = s.student_id
            WHERE a.date = %s
        """, (date,))
        
        attendance = cursor.fetchall()
        
        # Convert datetime objects to strings
        for record in attendance:
            if 'date' in record:
                record['date'] = str(record['date'])
        
        cursor.close()
        conn.close()
        
        return jsonify(attendance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO attendance (student_id, date, status, remarks)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE status=%s, remarks=%s
        """, (data['student_id'], data['date'], data['status'], 
              data.get('remarks', ''), data['status'], data.get('remarks', '')))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Attendance marked successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/student/<int:student_id>', methods=['GET'])
def get_student_attendance(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE student_id = %s 
            ORDER BY date DESC
        """, (student_id,))
        
        attendance = cursor.fetchall()
        
        # Convert dates to strings
        for record in attendance:
            if 'date' in record:
                record['date'] = str(record['date'])
        
        cursor.close()
        conn.close()
        
        return jsonify(attendance)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/graph/<int:student_id>', methods=['GET'])
def generate_attendance_graph(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get student info
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        
        # Get attendance data for last 30 days
        cursor.execute("""
            SELECT date, status FROM attendance 
            WHERE student_id = %s AND date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            ORDER BY date
        """, (student_id,))
        
        attendance_data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not attendance_data:
            return jsonify({'error': 'No attendance data found'}), 404
        
        # Prepare data for plotting
        dates = [str(record['date']) for record in attendance_data]
        statuses = [record['status'] for record in attendance_data]
        
        # Count status types
        present_count = statuses.count('Present')
        absent_count = statuses.count('Absent')
        late_count = statuses.count('Late')
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Pie chart
        labels = ['Present', 'Absent', 'Late']
        sizes = [present_count, absent_count, late_count]
        colors = ['#4CAF50', '#F44336', '#FF9800']
        explode = (0.1, 0, 0)
        
        ax1.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax1.set_title(f'Attendance Distribution - {student["name"]}')
        
        # Bar chart
        status_counts = {'Present': present_count, 'Absent': absent_count, 'Late': late_count}
        ax2.bar(status_counts.keys(), status_counts.values(), color=colors)
        ax2.set_ylabel('Count')
        ax2.set_title('Attendance Summary')
        ax2.grid(axis='y', alpha=0.3)
        
        # Calculate percentage
        total = sum(sizes)
        percentage = (present_count / total * 100) if total > 0 else 0
        fig.suptitle(f'Attendance: {percentage:.1f}% ({present_count}/{total} days)', 
                     fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save to bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Convert to base64
        img_base64 = base64.b64encode(buf.getvalue()).decode()
        
        return jsonify({
            'image': img_base64,
            'attendance_percentage': percentage,
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'total': total
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Total students
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        
        # Today's attendance
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT COUNT(*) as present FROM attendance 
            WHERE date = %s AND status = 'Present'
        """, (today,))
        present_today = cursor.fetchone()['present']
        
        cursor.execute("""
            SELECT COUNT(*) as absent FROM attendance 
            WHERE date = %s AND status = 'Absent'
        """, (today,))
        absent_today = cursor.fetchone()['absent']
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total_students': total_students,
            'present_today': present_today,
            'absent_today': absent_today
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)