const API_URL = 'http://localhost:5000/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    loadStats();
    loadStudents();
    setTodayDate();
    setupEventListeners();
});

// Tab functionality
function initializeTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab
            btn.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            
            // Load content based on tab
            if (tabName === 'students') {
                loadStudents();
            } else if (tabName === 'attendance') {
                loadAttendanceForm();
            } else if (tabName === 'reports') {
                loadReports();
            }
        });
    });
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('searchInput').addEventListener('input', debounce(loadStudents, 300));
    document.getElementById('sortSelect').addEventListener('change', loadStudents);
    document.getElementById('attendanceDate').addEventListener('change', loadAttendanceForm);
    document.getElementById('addStudentForm').addEventListener('submit', handleAddStudent);
}

// Debounce function for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/stats`);
        const data = await response.json();
        
        document.getElementById('totalStudents').textContent = data.total_students;
        document.getElementById('presentToday').textContent = data.present_today;
        document.getElementById('absentToday').textContent = data.absent_today;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load students with search and sort
async function loadStudents() {
    const searchInput = document.getElementById('searchInput').value;
    const sortSelect = document.getElementById('sortSelect').value;
    const [sortBy, order] = sortSelect.split('-');
    
    try {
        const url = `${API_URL}/students?search=${searchInput}&sort_by=${sortBy}&order=${order}`;
        const response = await fetch(url);
        const students = await response.json();
        
        displayStudents(students);
    } catch (error) {
        console.error('Error loading students:', error);
        document.getElementById('studentsList').innerHTML = '<p>Error loading students</p>';
    }
}

// Display students
function displayStudents(students) {
    const container = document.getElementById('studentsList');
    
    if (students.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999;">No students found</p>';
        return;
    }
    
    container.innerHTML = students.map(student => `
        <div class="student-card">
            <h3>${student.name}</h3>
            <p><strong>Roll:</strong> ${student.roll_number}</p>
            <p><strong>Class:</strong> ${student.class}</p>
            <p><strong>Email:</strong> ${student.email}</p>
            <button class="btn btn-primary" onclick="viewAttendance(${student.student_id}, '${student.name}')">
                View Attendance
            </button>
        </div>
    `).join('');
}

// Add student form handlers
function showAddStudentForm() {
    document.getElementById('addStudentModal').style.display = 'block';
}

function closeAddStudentForm() {
    document.getElementById('addStudentModal').style.display = 'none';
    document.getElementById('addStudentForm').reset();
}

async function handleAddStudent(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const studentData = {
        name: formData.get('name'),
        roll_number: formData.get('roll_number'),
        class: formData.get('class'),
        email: formData.get('email')
    };
    
    try {
        const response = await fetch(`${API_URL}/students`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(studentData)
        });
        
        if (response.ok) {
            alert('Student added successfully!');
            closeAddStudentForm();
            loadStudents();
            loadStats();
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        console.error('Error adding student:', error);
        alert('Error adding student');
    }
}

// Set today's date
function setTodayDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('attendanceDate').value = today;
}

// Load attendance form
async function loadAttendanceForm() {
    try {
        const studentsResponse = await fetch(`${API_URL}/students`);
        const students = await studentsResponse.json();
        
        const date = document.getElementById('attendanceDate').value;
        const attendanceResponse = await fetch(`${API_URL}/attendance?date=${date}`);
        const attendanceRecords = await attendanceResponse.json();
        
        displayAttendanceForm(students, attendanceRecords);
    } catch (error) {
        console.error('Error loading attendance:', error);
    }
}

// Display attendance form
function displayAttendanceForm(students, attendanceRecords) {
    const container = document.getElementById('attendanceList');
    
    if (students.length === 0) {
        container.innerHTML = '<p style="text-align: center;">No students available</p>';
        return;
    }
    
    container.innerHTML = students.map(student => {
        const record = attendanceRecords.find(r => r.student_id === student.student_id);
        const status = record ? record.status : 'Present';
        
        return `
            <div class="attendance-item">
                <div class="attendance-info">
                    <h4>${student.name}</h4>
                    <p>${student.roll_number} - ${student.class}</p>
                </div>
                <div class="attendance-status">
                    <select id="status-${student.student_id}">
                        <option value="Present" ${status === 'Present' ? 'selected' : ''}>Present</option>
                        <option value="Absent" ${status === 'Absent' ? 'selected' : ''}>Absent</option>
                        <option value="Late" ${status === 'Late' ? 'selected' : ''}>Late</option>
                    </select>
                </div>
                <div class="attendance-actions">
                    <button class="btn btn-success" onclick="markAttendance(${student.student_id})">
                        Save
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Mark attendance
async function markAttendance(studentId) {
    const status = document.getElementById(`status-${studentId}`).value;
    const date = document.getElementById('attendanceDate').value;
    
    try {
        const response = await fetch(`${API_URL}/attendance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                student_id: studentId,
                date: date,
                status: status,
                remarks: ''
            })
        });
        
        if (response.ok) {
            alert('Attendance marked successfully!');
            loadStats();
        } else {
            alert('Error marking attendance');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error marking attendance');
    }
}

// Load reports
async function loadReports() {
    try {
        const response = await fetch(`${API_URL}/students`);
        const students = await response.json();
        
        displayReports(students);
    } catch (error) {
        console.error('Error loading reports:', error);
    }
}

// Display reports
function displayReports(students) {
    const container = document.getElementById('reportsList');
    
    container.innerHTML = students.map(student => `
        <div class="report-card" onclick="viewAttendanceGraph(${student.student_id}, '${student.name}')">
            <h3>${student.name}</h3>
            <p>${student.roll_number}</p>
            <p>${student.class}</p>
            <p style="margin-top: 10px;">📊 Click to view attendance graph</p>
        </div>
    `).join('');
}

// View attendance (simple version)
async function viewAttendance(studentId, studentName) {
    try {
        const response = await fetch(`${API_URL}/attendance/student/${studentId}`);
        const records = await response.json();
        
        if (records.length === 0) {
            alert('No attendance records found for this student');
            return;
        }
        
        let message = `Attendance Record for ${studentName}\n\n`;
        records.forEach(record => {
            message += `${record.date}: ${record.status}\n`;
        });
        
        alert(message);
    } catch (error) {
        console.error('Error:', error);
    }
}

// View attendance graph
async function viewAttendanceGraph(studentId, studentName) {
    try {
        const response = await fetch(`${API_URL}/attendance/graph/${studentId}`);
        const data = await response.json();
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        const modal = document.getElementById('graphModal');
        const graphContainer = document.getElementById('graphContainer');
        
        graphContainer.innerHTML = `
            <div class="attendance-stats">
                <div class="stat-box">
                    <h4>${data.attendance_percentage.toFixed(1)}%</h4>
                    <p>Attendance</p>
                </div>
                <div class="stat-box">
                    <h4>${data.present}</h4>
                    <p>Present</p>
                </div>
                <div class="stat-box">
                    <h4>${data.absent}</h4>
                    <p>Absent</p>
                </div>
                <div class="stat-box">
                    <h4>${data.late}</h4>
                    <p>Late</p>
                </div>
            </div>
            <img src="data:image/png;base64,${data.image}" alt="Attendance Graph">
        `;
        
        document.getElementById('graphTitle').textContent = `Attendance Report - ${studentName}`;
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error loading graph:', error);
        alert('Error loading attendance graph');
    }
}

// Close graph modal
function closeGraphModal() {
    document.getElementById('graphModal').style.display = 'none';
}

// Close modal on outside click
window.onclick = function(event) {
    const addModal = document.getElementById('addStudentModal');
    const graphModal = document.getElementById('graphModal');
    
    if (event.target === addModal) {
        closeAddStudentForm();
    }
    if (event.target === graphModal) {
        closeGraphModal();
    }
}