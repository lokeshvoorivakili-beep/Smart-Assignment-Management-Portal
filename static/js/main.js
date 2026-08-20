/* Smart Assignment Management Portal - Main JavaScript Engine */

// Global State
let currentStudentAssignment = null;
let currentFacultyAssignment = null;
let currentGradeSubmissionId = null;
let currentGradedFilename = null;
let currentInstructionFilename = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDepartments();
    checkActiveSession();
});

/* ── NAVIGATION ── */
function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(id);
    if (target) {
        target.classList.add('active');
        window.scrollTo(0, 0);
        sessionStorage.setItem('lastActiveScreen', id);
    }
    if (id === 'screen-faculty-create') {
        const deadlineInput = document.getElementById('create-deadline');
        if (deadlineInput) {
            const now = new Date();
            const minNow = new Date(now);
            minNow.setMinutes(minNow.getMinutes() - minNow.getTimezoneOffset());
            deadlineInput.min = minNow.toISOString().slice(0, 16);

            if (!deadlineInput.value) {
                const future = new Date(now);
                future.setDate(future.getDate() + 7);
                future.setMinutes(future.getMinutes() - future.getTimezoneOffset());
                deadlineInput.value = future.toISOString().slice(0, 16);
            }
        }
    }
}

function switchAuthTab(el, panelId) {
    const card = el.closest('.auth-card');
    card.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    card.querySelectorAll('.register-panel').forEach(p => p.classList.remove('active'));
    el.classList.add('active');
    card.querySelector('#' + panelId).classList.add('active');
}

function switchTab(el, panelId) {
    const parent = el.closest('.page-content, .screen');
    parent.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
    parent.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    el.classList.add('active');
    const panel = parent.querySelector('#' + panelId);
    if (panel) panel.classList.add('active');
}

/* JNTUA R24 B.Tech Subjects Data Map for 7 Branches */
const JNTUA_R24_SUBJECTS = {
  'CSE': {
    '1': [
      "Communicative English", "Linear Algebra & Calculus", "Engineering Physics",
      "Basic Civil & Mechanical Engineering", "Introduction to Programming", "Chemistry",
      "Differential Equations & Vector Calculus", "Basic Electrical & Electronics Engineering",
      "Data Structures", "Engineering Graphics"
    ],
    '2': [
      "Discrete Mathematics & Graph Theory", "Digital Logic Design", "Computer Organization & Architecture",
      "Object Oriented Programming through Java", "Universal Human Values", "Database Management Systems",
      "Design and Analysis of Algorithms", "Operating Systems", "Software Engineering",
      "Managerial Economics & Financial Analysis"
    ],
    '3': [
      "Computer Networks", "Formal Languages and Automata Theory", "Artificial Intelligence",
      "Cloud Computing", "Software Testing", "Advanced Data Structures", "Compiler Design",
      "Machine Learning", "Cryptography and Network Security", "Full Stack Web Development",
      "Mobile Application Development", "DevOps"
    ],
    '4': [
      "Big Data Analytics", "Deep Learning", "Internet of Things", "Natural Language Processing",
      "Cyber Security", "Blockchain Technology", "High Performance Computing", "Generative AI",
      "Reinforcement Learning"
    ]
  },
  'AIML': {
    '1': [
      "Communicative English", "Linear Algebra & Calculus", "Engineering Physics",
      "Basic Civil & Mechanical Engineering", "Introduction to Programming", "Chemistry",
      "Differential Equations & Vector Calculus", "Basic Electrical & Electronics Engineering",
      "Data Structures", "Engineering Graphics"
    ],
    '2': [
      "Mathematical Foundations of Computer Science", "Digital Logic Design", "Computer Organization & Architecture",
      "Object Oriented Programming through Java", "Universal Human Values", "Database Management Systems",
      "Design and Analysis of Algorithms", "Operating Systems", "Artificial Intelligence Concepts & Logic",
      "Managerial Economics & Financial Analysis"
    ],
    '3': [
      "Computer Networks", "Machine Learning Techniques", "Knowledge Representation and Reasoning",
      "Computer Vision", "Optimization Techniques", "Pattern Recognition", "Deep Learning Architecture",
      "Natural Language Processing", "Reinforcement Learning", "AI in Healthcare", "Speech & Audio Processing"
    ],
    '4': [
      "Big Data Analytics for AI", "Generative AI", "AI Ethics & Governance", "Soft Computing",
      "AI in Robotics", "Autonomous Systems", "Neural Networks", "Explainable AI", "MLOps"
    ]
  },
  'DS': {
    '1': [
      "Communicative English", "Linear Algebra & Calculus", "Engineering Physics",
      "Basic Civil & Mechanical Engineering", "Introduction to Programming", "Chemistry",
      "Differential Equations & Vector Calculus", "Basic Electrical & Electronics Engineering",
      "Data Structures", "Engineering Graphics"
    ],
    '2': [
      "Probability & Statistics for Data Science", "Digital Logic Design", "Computer Organization & Architecture",
      "Object Oriented Programming through Java", "Universal Human Values", "Database Management Systems",
      "Design and Analysis of Algorithms", "Operating Systems", "Principles of Data Science",
      "Managerial Economics & Financial Analysis"
    ],
    '3': [
      "Computer Networks", "Data Mining and Data Warehousing", "Machine Learning for Data Science",
      "R Programming for Data Analytics", "Exploratory Data Analysis", "NoSQL Databases",
      "Big Data Analytics", "Predictive Analytics", "Data Visualization Techniques",
      "Time Series Analysis", "Business Intelligence"
    ],
    '4': [
      "Deep Learning for Analytics", "Cloud Data Analytics", "Social Media Analytics",
      "Data Security and Privacy", "Natural Language Processing", "Stream Analytics",
      "Text Mining", "Web Analytics", "Financial Data Analytics"
    ]
  },
  'ECE': {
    '1': [
      "Communicative English", "Linear Algebra & Calculus", "Chemistry",
      "Basic Electrical & Electronics Engineering", "Introduction to Programming", "Engineering Physics",
      "Differential Equations & Vector Calculus", "Basic Civil & Mechanical Engineering",
      "Data Structures", "Engineering Graphics"
    ],
    '2': [
      "Electronic Devices and Circuits", "Network Analysis & Synthesis", "Signals and Systems",
      "Digital Logic Design", "Universal Human Values", "Analog Circuits",
      "Electromagnetic Waves and Transmission Lines", "Control Systems", "Probability Theory & Stochastic Processes",
      "Managerial Economics & Financial Analysis"
    ],
    '3': [
      "Digital Signal Processing", "Analog & Digital Communications", "Microprocessors and Microcontrollers",
      "VLSI Design", "Antennas & Wave Propagation", "Linear IC Applications", "Microwave Engineering",
      "Computer Networks", "Embedded Systems", "Digital Image Processing", "Optical Communications"
    ],
    '4': [
      "Wireless & Mobile Communications", "Cellular & Mobile Communications", "RF Circuit Design",
      "Satellite Communications", "Radar Engineering", "Internet of Things", "Information Theory and Coding",
      "System on Chip", "5G Wireless Technology"
    ]
  },
  'EEE': {
    '1': [
      "Communicative English", "Linear Algebra & Calculus", "Chemistry",
      "Basic Electrical & Electronics Engineering", "Introduction to Programming", "Engineering Physics",
      "Differential Equations & Vector Calculus", "Basic Civil & Mechanical Engineering",
      "Data Structures", "Engineering Graphics"
    ],
    '2': [
      "Electrical Circuit Analysis", "DC Machines and Transformers", "Electromagnetic Fields",
      "Electronic Devices and Circuits", "Universal Human Values", "AC Machines",
      "Power System Generation and Transmission", "Control Systems", "Analog Electronics",
      "Managerial Economics & Financial Analysis"
    ],
    '3': [
      "Power Electronics", "Power System Analysis", "Microprocessors and Microcontrollers",
      "Electrical Measurements & Instrumentation", "Signals and Systems", "Linear System Theory",
      "Power System Protection and Switchgear", "Electric Drives and Control", "Digital Signal Processing",
      "Special Electrical Machines", "Power Quality"
    ],
    '4': [
      "High Voltage Engineering", "Renewable Energy Sources", "Smart Grid Technologies",
      "Flexible AC Transmission Systems", "Electric Vehicles", "HVDC Transmission",
      "Energy Management & Audit", "Microgrid Systems"
    ]
  },
  'MECH': {
    '1': [
      "Communicative English", "Linear Algebra & Calculus", "Engineering Physics",
      "Basic Civil & Mechanical Engineering", "Introduction to Programming", "Chemistry",
      "Differential Equations & Vector Calculus", "Basic Electrical & Electronics Engineering",
      "Engineering Graphics", "Engineering Mechanics"
    ],
    '2': [
      "Thermodynamics", "Mechanics of Solids", "Material Science and Metallurgy",
      "Manufacturing Processes", "Universal Human Values", "Applied Thermodynamics",
      "Fluid Mechanics and Hydraulic Machines", "Kinematics of Machinery",
      "Machine Drawing & Computer Aided Drafting", "Managerial Economics & Financial Analysis"
    ],
    '3': [
      "Dynamics of Machinery", "Heat Transfer", "Design of Machine Members - I",
      "Industrial Engineering & Management", "Metrology & Instrumentation", "Production Technology",
      "Design of Machine Members - II", "Machining & Machine Tools", "Operations Research",
      "CAD/CAM", "IC Engines", "Refrigeration and Air Conditioning"
    ],
    '4': [
      "Finite Element Methods", "Automation in Manufacturing", "Robotics & Mechatronics",
      "Automobile Engineering", "Additive Manufacturing", "Computational Fluid Dynamics",
      "Power Plant Engineering", "Tribology"
    ]
  },
  'CIVIL': {
    '1': [
      "Communicative English", "Linear Algebra & Calculus", "Engineering Physics",
      "Basic Civil & Mechanical Engineering", "Introduction to Programming", "Chemistry",
      "Differential Equations & Vector Calculus", "Basic Electrical & Electronics Engineering",
      "Engineering Graphics", "Engineering Mechanics"
    ],
    '2': [
      "Surveying and Geomatics", "Strength of Materials - I", "Fluid Mechanics",
      "Building Materials and Construction", "Universal Human Values", "Strength of Materials - II",
      "Hydraulics and Hydraulic Machinery", "Structural Analysis - I", "Environmental Engineering - I",
      "Managerial Economics & Financial Analysis"
    ],
    '3': [
      "Structural Analysis - II", "Concrete Technology", "Design of Reinforced Concrete Structures",
      "Geotechnical Engineering - I", "Transportation Engineering - I", "Water Resources Engineering - I",
      "Geotechnical Engineering - II", "Transportation Engineering - II", "Design of Steel Structures",
      "Remote Sensing and GIS", "Advanced Structural Analysis"
    ],
    '4': [
      "Estimation, Costing and Valuation", "Construction Technology and Project Management",
      "Pavement Analysis & Design", "Ground Improvement Techniques", "Irrigation Engineering",
      "Bridge Engineering", "Earthquake Resistant Design of Structures", "Solid Waste Management",
      "Pre-stressed Concrete"
    ]
  }
};

let departmentCodeMap = {};

/* ── DEPARTMENTS LOADER ── */
async function loadDepartments() {
    try {
        const res = await fetch('/api/departments');
        const data = await res.json();
        if (data.success) {
            const studentSelect = document.getElementById('sr-dept');
            const facultySelect = document.getElementById('fr-dept');
            const createDeptSelect = document.getElementById('create-dept');

            let html = '<option value="">— Select Department —</option>';
            data.departments.forEach(d => {
                departmentCodeMap[d.department_id] = d.code;
                html += `<option value="${d.department_id}">${d.code} - ${d.department_name}</option>`;
            });

            if (studentSelect) studentSelect.innerHTML = html;
            if (facultySelect) facultySelect.innerHTML = html;
            if (createDeptSelect) {
                createDeptSelect.innerHTML = html;
                updateCreateSubjectDropdown();
            }
        }
    } catch (e) {
        console.error("Failed to load departments", e);
    }
}

function updateCreateSubjectDropdown() {
    const deptSelect = document.getElementById('create-dept');
    const yearSelect = document.getElementById('create-year');
    const subjectSelect = document.getElementById('create-subject');
    const customInput = document.getElementById('create-custom-subject');

    if (!subjectSelect) return;

    const deptId = deptSelect ? deptSelect.value : '';
    const year = yearSelect ? yearSelect.value : '3';
    const deptCode = departmentCodeMap[deptId] || 'CSE';

    const subjects = (JNTUA_R24_SUBJECTS[deptCode] && JNTUA_R24_SUBJECTS[deptCode][year]) 
                     ? JNTUA_R24_SUBJECTS[deptCode][year] 
                     : (JNTUA_R24_SUBJECTS['CSE'][year] || []);

    let html = '<option value="">— Select JNTUA R24 Subject —</option>';
    subjects.forEach(sub => {
        html += `<option value="${sub}">${sub}</option>`;
    });
    html += '<option value="__custom__">+ Type Custom Subject Name...</option>';

    subjectSelect.innerHTML = html;
    if (customInput) customInput.style.display = 'none';
}

function handleSubjectSelectChange(select) {
    const customInput = document.getElementById('create-custom-subject');
    if (customInput) {
        if (select.value === '__custom__') {
            customInput.style.display = 'block';
            customInput.focus();
        } else {
            customInput.style.display = 'none';
        }
    }
}

/* ── REAL-TIME AUTO-REFRESHER ENGINE (NO LOGOUT NEEDED) ── */
let liveAutoRefreshInterval = null;

function startLiveAutoRefresher() {
    if (liveAutoRefreshInterval) clearInterval(liveAutoRefreshInterval);
    
    // Poll every 10 seconds for live real-time background updates without disturbing scroll or inputs
    liveAutoRefreshInterval = setInterval(() => {
        const activeScreen = document.querySelector('.screen.active');
        if (!activeScreen) return;
        const screenId = activeScreen.id;

        if (screenId === 'screen-student-dashboard') {
            loadStudentAssignments();
        } else if (screenId === 'screen-faculty-dashboard') {
            loadFacultyAssignments();
        } else if (screenId === 'screen-admin-dashboard') {
            loadAdminDashboard();
        }
    }, 10000);
}

window.addEventListener('focus', () => {
    const activeScreen = document.querySelector('.screen.active');
    if (!activeScreen) return;
    const screenId = activeScreen.id;
    if (screenId === 'screen-student-dashboard') loadStudentAssignments();
    if (screenId === 'screen-faculty-dashboard') loadFacultyAssignments();
    if (screenId === 'screen-admin-dashboard') loadAdminDashboard();
});

/* ── SESSION CHECK ── */
async function checkActiveSession() {
    startLiveAutoRefresher();
    try {
        const sRes = await fetch('/api/student/session');
        const sData = await sRes.json();
        if (sData.logged_in) {
            updateStudentUI(sData);
            await loadStudentAssignments();
            const savedScreen = sessionStorage.getItem('lastActiveScreen');
            const savedStudentAsgnId = sessionStorage.getItem('lastStudentAssignmentId');
            if (savedScreen === 'screen-student-detail' && savedStudentAsgnId) {
                await openStudentDetail(savedStudentAsgnId);
            } else if (savedScreen && document.getElementById(savedScreen)) {
                showScreen(savedScreen);
            } else {
                showScreen('screen-student-dashboard');
            }
            return;
        }

        const fRes = await fetch('/api/faculty/session');
        const fData = await fRes.json();
        if (fData.logged_in) {
            updateFacultyUI(fData);
            await loadFacultyAssignments();
            const savedScreen = sessionStorage.getItem('lastActiveScreen');
            const savedFacultyAsgnId = sessionStorage.getItem('lastFacultyAssignmentId');
            if (savedScreen === 'screen-faculty-submissions' && savedFacultyAsgnId) {
                await openFacultySubmissions(savedFacultyAsgnId);
            } else if (savedScreen && document.getElementById(savedScreen)) {
                showScreen(savedScreen);
            } else {
                showScreen('screen-faculty-dashboard');
            }
            return;
        }
    } catch (e) {
        console.error("Error checking session", e);
    }
}

/* ── TOAST NOTIFICATION ── */
let toastTimer;
function showToast(msg) {
    const t = document.getElementById('toast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 3000);
}

/* ── LOGOUT ── */
async function handleLogout() {
    sessionStorage.clear();
    await fetch('/api/student/logout', { method: 'POST' });
    await fetch('/api/faculty/logout', { method: 'POST' });
    await fetch('/api/admin/logout', { method: 'POST' });
    showToast('Logged out successfully.');
    showScreen('screen-home');
}

/* ==========================================
   STUDENT MODULE
   ========================================== */

async function handleStudentLogin(e) {
    e.preventDefault();
    const hall_ticket_no = document.getElementById('s-hallticket').value.trim();
    const password = document.getElementById('s-pass').value.trim();

    if (!hall_ticket_no || !password) {
        showToast('Please enter Hall Ticket Number and Password.');
        return;
    }

    showToast('Signing in…');

    try {
        const res = await fetch('/api/student/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hall_ticket_no, password })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Welcome back, ' + data.student.name);
            updateStudentUI(data.student);
            startLiveAutoRefresher();
            loadStudentAssignments();
            showScreen('screen-student-dashboard');
        } else {
            showToast(data.message || 'Login failed.');
        }
    } catch (err) {
        showToast('Connection error. Please try again.');
    }
}

async function handleStudentRegister(e) {
    e.preventDefault();
    const payload = {
        first_name: document.getElementById('sr-firstname').value.trim(),
        last_name: document.getElementById('sr-lastname').value.trim(),
        hall_ticket_no: document.getElementById('sr-hallticket').value.trim(),
        email: document.getElementById('sr-email').value.trim(),
        phone: document.getElementById('sr-phone').value.trim(),
        department_id: document.getElementById('sr-dept').value,
        year: document.getElementById('sr-year').value,
        section: document.getElementById('sr-section').value,
        password: document.getElementById('sr-pass').value.trim()
    };

    try {
        const res = await fetch('/api/student/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            setTimeout(() => {
                switchAuthTab(document.querySelector('.auth-tab'), 's-login');
            }, 1500);
        } else {
            showToast(data.message || 'Registration failed.');
        }
    } catch (err) {
        showToast('Registration error.');
    }
}

function updateStudentUI(student) {
    const avatar = document.getElementById('s-avatar');
    const heroTitle = document.getElementById('s-hero-title');
    const eyebrow = document.getElementById('s-eyebrow');

    if (avatar) avatar.textContent = (student.name || 'S').charAt(0).toUpperCase();
    if (heroTitle) heroTitle.textContent = `${student.name}'s Assignments`;
    if (eyebrow) {
        eyebrow.innerHTML = `<span>${student.dept_code || student.dept}</span><span>Year ${student.year}</span><span>Section ${student.section}</span>`;
    }
    const sdEyebrow = document.getElementById('sd-eyebrow');
    if (sdEyebrow) {
        sdEyebrow.innerHTML = `<span>${student.dept_code || student.dept}</span><span>Year ${student.year}</span><span>Section ${student.section}</span>`;
    }
}

async function loadStudentAssignments() {
    updateNotificationBadge();
    try {
        const res = await fetch('/api/student/assignments');
        const data = await res.json();
        if (!data.success) return;

        const openList = document.getElementById('s-open-list');
        const closedList = document.getElementById('s-closed-list');
        const gradesList = document.getElementById('s-grades-list');

        let openHtml = '';
        let closedHtml = '';

        data.assignments.forEach(a => {
            const cardHtml = `
                <div class="asgn-card" data-subject="${a.subject}" onclick="openStudentDetail(${a.assignment_id})">
                    <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">
                        <div class="status-badge ${a.is_open ? 'status-open' : 'status-closed'}">${a.is_open ? 'Open' : 'Closed'}</div>
                        ${a.has_instruction_file ? '<span style="background:rgba(201,168,76,0.15);color:var(--gold);font-size:10px;font-weight:600;padding:2px 8px;border-radius:12px;border:1px solid rgba(201,168,76,0.3);">📎 Doc Attached</span>' : ''}
                    </div>
                    <div class="subject-tag">${a.subject}</div>
                    <div class="asgn-title">${a.title}</div>
                    <div class="asgn-meta">
                        <span>${a.dept_code}</span><span>Year ${a.year}</span><span>Sec ${a.section}</span><span>Max ${a.maximum_marks} marks</span>
                    </div>
                    <div class="asgn-deadline">
                        <span class="dot ${a.is_open ? 'dot-green' : 'dot-red'}"></span>
                        <span>${a.is_open ? 'Due ' + a.deadline : 'Deadline passed: ' + a.deadline}</span>
                    </div>
                    ${a.instruction_file ? `<button class="btn-new" style="margin-top:10px;font-size:11px;padding:6px 12px;width:100%;justify-content:center;" onclick="event.stopPropagation(); window.open('/download/assignment/${a.instruction_file}', '_blank');">📄 ↓ Download Faculty Document</button>` : ''}
                </div>
            `;
            if (a.is_open) openHtml += cardHtml;
            else closedHtml += cardHtml;
        });

        if (openList) openList.innerHTML = openHtml || '<p style="color:var(--text-muted)">No open assignments found.</p>';
        if (closedList) closedList.innerHTML = closedHtml || '<p style="color:var(--text-muted)">No closed assignments found.</p>';

        loadStudentGrades();
    } catch (e) {
        console.error("Error loading assignments", e);
    }
}

async function loadStudentGrades() {
    try {
        const res = await fetch('/api/student/grades');
        const data = await res.json();
        const gradesList = document.getElementById('s-grades-list');
        if (!gradesList) return;

        if (data.success && data.grades.length > 0) {
            let html = '';
            data.grades.forEach(g => {
                html += `
                    <div class="marks-card">
                        <div class="marks-score">${g.marks}<span>/${g.maximum_marks}</span></div>
                        <div class="marks-info">
                            <h4>${g.subject} — ${g.assignment_title}</h4>
                            <p>Graded by ${g.faculty_name} · ${g.graded_at}</p>
                            ${g.uploaded_file ? `<button class="btn-new" style="font-size:11px;padding:4px 10px;margin-top:6px;" onclick="window.open('/download/submission/${g.uploaded_file}', '_blank')">↓ Download Submitted File</button>` : ''}
                        </div>
                    </div>
                    <div class="feedback-box mt-8" style="margin-bottom:20px;">
                        <h4>Faculty Feedback</h4>
                        <p>${g.feedback || 'No written feedback provided.'}</p>
                    </div>
                `;
            });
            gradesList.innerHTML = html;
        } else {
            gradesList.innerHTML = '<p style="color:var(--text-muted)">No graded assignments available yet.</p>';
        }
    } catch (e) {
        console.error("Error loading grades", e);
    }
}

async function openStudentDetail(assignmentId) {
    try {
        const res = await fetch(`/api/student/assignments/${assignmentId}`);
        const data = await res.json();
        if (!data.success) {
            showToast(data.message);
            return;
        }

        const a = data.assignment;
        currentStudentAssignment = a;
        sessionStorage.setItem('lastStudentAssignmentId', assignmentId);

        document.getElementById('detail-subject-tag').textContent = a.subject;
        document.getElementById('detail-subject-tag').className = 'subject-tag subject-tag-' + a.subject;
        document.getElementById('detail-title').textContent = a.title;
        document.getElementById('detail-desc').textContent = a.description;
        document.getElementById('detail-marks').textContent = a.maximum_marks;
        document.getElementById('detail-deadline').textContent = a.deadline;

        const statusEl = document.getElementById('detail-status');
        if (statusEl) {
            statusEl.textContent = a.is_open ? 'Open' : 'Closed';
            statusEl.style.color = a.is_open ? '#2ecc71' : '#e74c3c';
        }

        const subStatusEl = document.getElementById('detail-sub-status');
        if (subStatusEl) {
            if (a.submission) {
                subStatusEl.textContent = `${a.submission.status} (${a.submission.filename})`;
                subStatusEl.style.color = 'var(--gold)';
            } else {
                subStatusEl.textContent = 'None yet';
                subStatusEl.style.color = 'var(--text-muted)';
            }
        }

        // Instruction file button
        const instContainer = document.getElementById('instruction-download-container');
        const btnDownload = document.getElementById('btn-download-instruction');
        if (instContainer) {
            instContainer.style.display = 'block';
            if (a.instruction_file) {
                btnDownload.style.display = 'inline-flex';
                btnDownload.innerHTML = '📄 ↓ Download Faculty Assignment Document';
                btnDownload.onclick = () => window.open(`/download/assignment/${a.instruction_file}`, '_blank');
            } else {
                btnDownload.style.display = 'none';
                instContainer.innerHTML = '<div style="font-size:12px;color:var(--text-muted);padding:8px 12px;background:rgba(255,255,255,0.03);border:1px dashed var(--border);border-radius:var(--radius);display:inline-block;">ℹ️ No document attached by faculty for this assignment</div>';
            }
        }

        // Upload zone & button state
        const submitBtn = document.getElementById('btn-submit-assignment');
        const zoneTitle = document.getElementById('upload-zone-title');
        if (!a.is_open) {
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.5';
            submitBtn.textContent = 'Deadline Passed';
            zoneTitle.textContent = 'Submission Closed';
        } else {
            submitBtn.disabled = false;
            submitBtn.style.opacity = '1';
            submitBtn.textContent = a.submission ? 'Re-Submit Assignment' : 'Submit Assignment';
            zoneTitle.textContent = a.submission ? 'Upload Re-Submission' : 'Upload Your Submission';
        }

        document.getElementById('upload-fname').style.display = 'none';
        document.getElementById('file-input').value = '';

        showScreen('screen-student-detail');
    } catch (e) {
        showToast('Error opening assignment.');
    }
}

function fileSelected(input) {
    const fname = input.files[0] ? input.files[0].name : '';
    const el = document.getElementById('upload-fname');
    if (el && fname) {
        el.textContent = '📎 ' + fname;
        el.style.display = 'block';
    }
}

async function submitStudentAssignment() {
    if (!currentStudentAssignment) return;
    const fileInput = document.getElementById('file-input');
    if (!fileInput.files || fileInput.files.length === 0) {
        showToast('Please select a file to upload.');
        return;
    }

    const formData = new FormData();
    formData.append('assignment_id', currentStudentAssignment.assignment_id);
    formData.append('file', fileInput.files[0]);

    showToast('Uploading submission…');

    try {
        const res = await fetch('/api/student/submit', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            if (data.similarity_score > 70) {
                showToast(`Submission recorded. Similarity score: ${data.similarity_score}%`);
            }
            setTimeout(() => {
                loadStudentAssignments();
                showScreen('screen-student-dashboard');
            }, 1500);
        } else {
            showToast(data.message || 'Submission failed.');
        }
    } catch (e) {
        showToast('Upload failed. Please check network.');
    }
}

/* ==========================================
   FACULTY MODULE
   ========================================== */

async function handleFacultyLogin(e) {
    e.preventDefault();
    const faculty_code = document.getElementById('f-id').value.trim();
    const password = document.getElementById('f-pass').value.trim();

    if (!faculty_code || !password) {
        showToast('Please enter Faculty ID and Password.');
        return;
    }

    showToast('Signing in…');

    try {
        const res = await fetch('/api/faculty/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ faculty_code, password })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Welcome back, ' + data.faculty.name);
            updateFacultyUI(data.faculty);
            loadFacultyAssignments();
            showScreen('screen-faculty-dashboard');
        } else {
            showToast(data.message || 'Faculty login failed.');
        }
    } catch (err) {
        showToast('Connection error.');
    }
}

async function handleFacultyRegister(e) {
    e.preventDefault();
    const payload = {
        first_name: document.getElementById('fr-firstname').value.trim(),
        last_name: document.getElementById('fr-lastname').value.trim(),
        faculty_code: document.getElementById('fr-code').value.trim(),
        email: document.getElementById('fr-email').value.trim(),
        phone: document.getElementById('fr-phone').value.trim(),
        department_id: document.getElementById('fr-dept').value,
        password: document.getElementById('fr-pass').value.trim()
    };

    try {
        const res = await fetch('/api/faculty/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            setTimeout(() => {
                switchAuthTab(document.querySelector('#screen-faculty-auth .auth-tab'), 'f-login');
            }, 1500);
        } else {
            showToast(data.message || 'Faculty registration failed.');
        }
    } catch (err) {
        showToast('Registration error.');
    }
}

function updateFacultyUI(faculty) {
    const avatar = document.getElementById('f-avatar');
    const eyebrow = document.getElementById('f-eyebrow');
    if (avatar) avatar.textContent = (faculty.name || 'F').charAt(0).toUpperCase();
    if (eyebrow) {
        eyebrow.innerHTML = `<span>${faculty.name}</span><span>${faculty.dept_code || faculty.dept}</span>`;
    }
}

async function loadFacultyAssignments() {
    try {
        const res = await fetch('/api/faculty/assignments');
        const data = await res.json();
        if (!data.success) return;

        const list = document.getElementById('faculty-asgn-list');
        if (!list) return;

        let html = '';
        data.assignments.forEach(a => {
            html += `
                <div class="asgn-card dark" data-subject="${a.subject}" onclick="openFacultySubmissions(${a.assignment_id})">
                    <div class="status-badge ${a.is_open ? 'status-open' : 'status-closed'}">${a.is_open ? 'Open' : 'Closed'}</div>
                    <div class="subject-tag">${a.subject}</div>
                    <div class="asgn-title">${a.title}</div>
                    <div class="asgn-meta"><span>${a.dept_code}</span><span>Year ${a.year}</span><span>Sec ${a.section}</span><span>Max ${a.maximum_marks} marks</span></div>
                    <div class="asgn-meta">${a.total_submissions} submission(s) · ${a.graded_count} graded</div>
                    <div class="asgn-deadline"><span class="dot ${a.is_open ? 'dot-green' : 'dot-red'}"></span><span>${a.is_open ? 'Due ' + a.deadline : 'Closed ' + a.deadline}</span></div>
                </div>
            `;
        });

        list.innerHTML = html || '<p style="color:var(--text-muted)">No assignments created yet. Click "+ New assignment" to post one.</p>';
    } catch (e) {
        console.error("Error loading faculty assignments", e);
    }
}

function filterFaculty(btn, subject) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const cards = document.querySelectorAll('#faculty-asgn-list .asgn-card');
    cards.forEach(card => {
        const match = subject === 'all' || card.dataset.subject === subject;
        card.style.display = match ? '' : 'none';
    });
}

function fileSelectedFaculty(input) {
    const fname = input.files[0] ? input.files[0].name : '';
    const el = document.getElementById('upload-fname-f');
    if (el && fname) {
        el.textContent = '📄 ' + fname;
        el.style.display = 'block';
    }
}

async function handleCreateAssignment(e) {
    e.preventDefault();
    let subjectVal = document.getElementById('create-subject').value;
    if (subjectVal === '__custom__') {
        subjectVal = document.getElementById('create-custom-subject').value.trim();
    }
    if (!subjectVal) {
        showToast('Please select or type a subject name.');
        return;
    }

    const formData = new FormData();
    formData.append('subject', subjectVal);
    formData.append('title', document.getElementById('create-title').value.trim());
    formData.append('description', document.getElementById('create-desc').value.trim());
    formData.append('department_id', document.getElementById('create-dept').value);
    formData.append('year', document.getElementById('create-year').value);
    formData.append('section', document.getElementById('create-section').value);
    formData.append('maximum_marks', document.getElementById('create-marks').value);
    formData.append('deadline', document.getElementById('create-deadline').value);

    const fileInput = document.getElementById('file-input-f');
    if (fileInput.files && fileInput.files[0]) {
        formData.append('file', fileInput.files[0]);
    }

    showToast('Publishing assignment…');

    try {
        const res = await fetch('/api/faculty/assignments/create', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            document.getElementById('form-create-assignment').reset();
            document.getElementById('upload-fname-f').style.display = 'none';
            setTimeout(() => {
                loadFacultyAssignments();
                showScreen('screen-faculty-dashboard');
            }, 1200);
        } else {
            showToast(data.message || 'Creation failed.');
        }
    } catch (err) {
        showToast('Error creating assignment.');
    }
}

async function openFacultySubmissions(assignmentId) {
    try {
        const res = await fetch(`/api/faculty/assignments/${assignmentId}/submissions`);
        const data = await res.json();
        if (!data.success) {
            showToast(data.message);
            return;
        }

        const a = data.assignment;
        a.assignment_id = assignmentId;
        currentFacultyAssignment = a;
        sessionStorage.setItem('lastFacultyAssignmentId', assignmentId);

        document.getElementById('fs-eyebrow').innerHTML = `<span>${a.dept_code}</span><span>Year ${a.year}</span><span>Section ${a.section}</span>`;
        document.getElementById('fs-title').textContent = `${a.subject} — ${a.title}`;
        document.getElementById('fs-total').textContent = data.submissions.length;
        document.getElementById('fs-maxmarks').textContent = a.maximum_marks;

        const rowsContainer = document.getElementById('fs-submissions-rows');
        let html = '';

        data.submissions.forEach(s => {
            const isAlert = s.similarity_score >= 70;
            const simBadge = isAlert ? `<span class="pill pill-red">High Sim: ${s.similarity_score}%</span>` : '';
            
            html += `
                <div class="table-row" onclick="openGradeModal(${s.submission_id}, '${s.student_name.replace(/'/g, "\\'")}', '${s.hall_ticket_no}', ${s.marks !== null ? s.marks : 'null'}, '${(s.feedback || '').replace(/'/g, "\\'")}', '${s.uploaded_file}', ${s.similarity_score}, ${a.maximum_marks})">
                    <div>${s.student_name} <span style="font-size:11px;color:var(--text-muted)">${s.hall_ticket_no}</span> ${simBadge}</div>
                    <div>${s.submitted_at}</div>
                    <div><span class="pill ${s.is_graded ? 'pill-green' : 'pill-amber'}">${s.is_graded ? 'Graded' : 'Pending'}</span></div>
                    <div>${s.marks !== null ? s.marks + '/' + a.maximum_marks : '—'}</div>
                </div>
            `;
        });

        rowsContainer.innerHTML = html || '<p style="padding:20px;color:var(--text-muted)">No student submissions yet for this assignment.</p>';
        showScreen('screen-faculty-submissions');
    } catch (e) {
        showToast('Error opening submissions.');
    }
}

function openGradeModal(subId, name, hallTicket, marks, feedback, filename, simScore, maxMarks) {
    currentGradeSubmissionId = subId;
    currentGradedFilename = filename;

    document.getElementById('modal-student-name').textContent = `${name} · ${hallTicket}`;
    const marksInput = document.getElementById('modal-marks');
    marksInput.max = maxMarks;
    marksInput.value = marks !== null ? marks : '';
    document.getElementById('modal-feedback').value = feedback || '';

    const simBadge = document.getElementById('modal-similarity-badge');
    if (simScore >= 70) {
        simBadge.style.display = 'block';
        simBadge.innerHTML = `<span class="pill pill-red">⚠️ High Text Similarity Detected: ${simScore}%</span>`;
    } else {
        simBadge.style.display = 'none';
    }

    const downloadBtn = document.getElementById('btn-download-submission');
    downloadBtn.onclick = () => window.open(`/download/submission/${filename}`, '_blank');

    document.getElementById('grade-modal').classList.add('open');
}

function closeModal() {
    const modal = document.getElementById('grade-modal');
    if (modal) modal.classList.remove('open');
}

async function handleGradeSubmit(e) {
    e.preventDefault();
    if (!currentGradeSubmissionId) return;

    const marks = document.getElementById('modal-marks').value;
    const feedback = document.getElementById('modal-feedback').value.trim();

    try {
        const res = await fetch(`/api/faculty/submissions/${currentGradeSubmissionId}/grade`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ marks, feedback })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Grade saved and student notified!');
            closeModal();
            if (currentFacultyAssignment) {
                loadFacultyAssignments();
            }
        } else {
            showToast(data.message || 'Grading failed.');
        }
    } catch (err) {
        showToast('Error saving grade.');
    }
}

/* ==========================================
   ADMIN MODULE
   ========================================== */

async function handleAdminLogin(e) {
    e.preventDefault();
    const username = document.getElementById('a-username').value.trim();
    const password = document.getElementById('a-pass').value.trim();

    showToast('Signing in as Admin…');

    try {
        const res = await fetch('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Admin access granted.');
            loadAdminDashboard();
            showScreen('screen-admin-dashboard');
        } else {
            showToast(data.message || 'Admin login failed.');
        }
    } catch (err) {
        showToast('Connection error.');
    }
}

async function loadAdminDashboard() {
    try {
        // Stats
        const sRes = await fetch('/api/admin/dashboard-stats');
        const sData = await sRes.json();
        if (sData.success) {
            document.getElementById('adm-stat-students').textContent = sData.stats.total_students;
            document.getElementById('adm-stat-pstudents').textContent = sData.stats.pending_students;
            document.getElementById('adm-stat-faculty').textContent = sData.stats.total_faculty;
            document.getElementById('adm-stat-pfaculty').textContent = sData.stats.pending_faculty;
            document.getElementById('adm-stat-assignments').textContent = sData.stats.total_assignments;
            document.getElementById('adm-stat-submissions').textContent = sData.stats.total_submissions;
        }

        // Pending Registrations
        const pRes = await fetch('/api/admin/pending-registrations');
        const pData = await pRes.json();
        const pendingContainer = document.getElementById('admin-pending-rows');
        if (pData.success && pendingContainer) {
            let html = '';
            pData.pending.forEach(p => {
                html += `
                    <div class="admin-table-row" id="p-row-${p.type}-${p.id}">
                        <div>${p.name} <span style="font-size:11px;color:var(--text-muted)">(${p.identifier})</span></div>
                        <div>${p.role_dept}</div>
                        <div>${p.created_at}</div>
                        <div>
                            <button class="btn-approve" onclick="adminApprove('${p.type}', ${p.id}, '${p.name.replace(/'/g, "\\'")}')">Approve</button>
                            <button class="btn-reject" onclick="adminReject('${p.type}', ${p.id})">Reject</button>
                        </div>
                    </div>
                `;
            });
            pendingContainer.innerHTML = html || '<p style="padding:20px;color:var(--text-muted)">No pending user registration requests.</p>';
        }

        // Departments
        const dRes = await fetch('/api/admin/departments');
        const dData = await dRes.json();
        const deptContainer = document.getElementById('admin-dept-rows');
        if (dData.success && deptContainer) {
            let html = '';
            dData.departments.forEach(d => {
                html += `
                    <div class="table-row" style="grid-template-columns:2fr 1fr 1fr;cursor:default;">
                        <div>${d.department_name} (${d.code})</div>
                        <div>${d.student_count || 0}</div>
                        <div>${d.faculty_count || 0}</div>
                    </div>
                `;
            });
            deptContainer.innerHTML = html;
        }

        // Activity Log
        const logRes = await fetch('/api/admin/activity-logs');
        const logData = await logRes.json();
        const logContainer = document.getElementById('admin-activity-rows');
        if (logData.success && logContainer) {
            let html = '';
            logData.logs.forEach(l => {
                html += `
                    <div class="table-row" style="grid-template-columns:2fr 2fr 1fr;cursor:default;">
                        <div>${l.event_type} — ${l.description}</div>
                        <div>${l.user_name} (${l.user_role})</div>
                        <div>${l.created_at}</div>
                    </div>
                `;
            });
            logContainer.innerHTML = html || '<p style="padding:20px;color:var(--text-muted)">No recent activity recorded.</p>';
        }
    } catch (e) {
        console.error("Error loading admin dashboard", e);
    }
}

async function adminApprove(type, id, name) {
    try {
        const url = type === 'student' ? `/api/admin/students/${id}/approve` : `/api/admin/faculty/${id}/approve`;
        const res = await fetch(url, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast(`${name} approved ✓`);
            loadAdminDashboard();
        } else {
            showToast(data.message || 'Approval failed.');
        }
    } catch (e) {
        showToast('Action failed.');
    }
}

async function adminReject(type, id) {
    try {
        const url = type === 'student' ? `/api/admin/students/${id}/reject` : `/api/admin/faculty/${id}/reject`;
        const res = await fetch(url, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast('Registration rejected.');
            loadAdminDashboard();
        } else {
            showToast(data.message || 'Rejection failed.');
        }
    } catch (e) {
        showToast('Action failed.');
    }
}

async function promptAddDepartment() {
    const code = prompt("Enter 3-5 letter Department Code (e.g. AI):");
    if (!code) return;
    const name = prompt("Enter Full Department Name (e.g. Artificial Intelligence):");
    if (!name) return;

    try {
        const res = await fetch('/api/admin/departments/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, name })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            loadDepartments();
            loadAdminDashboard();
        } else {
            showToast(data.message || 'Failed to add department.');
        }
    } catch (e) {
        showToast('Error adding department.');
    }
}

/* ==========================================
   NOTIFICATIONS DRAWER ENGINE
   ========================================== */

async function openNotif(role) {
    const overlay = document.getElementById('notif-overlay');
    const container = document.getElementById('notif-items-container');
    if (!overlay || !container) return;

    overlay.classList.add('open');
    container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">Loading notifications…</p>';

    try {
        const url = role === 'Student' ? '/api/student/notifications' : '/api/student/notifications';
        const res = await fetch(url);
        const data = await res.json();
        if (data.success && data.notifications.length > 0) {
            let html = '';
            data.notifications.forEach(n => {
                html += `
                    <div class="notif-item">
                        <div class="notif-item-title">${n.title}</div>
                        <div class="notif-item-sub">${n.message} · ${n.time}</div>
                    </div>
                `;
            });
            container.innerHTML = html;
            const sBadge = document.getElementById('s-notif-count');
            if (sBadge) sBadge.textContent = data.notifications.length;
        } else {
            container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;padding:12px 0;">No notifications at this time.</p>';
            const sBadge = document.getElementById('s-notif-count');
            if (sBadge) sBadge.textContent = '0';
        }
    } catch (e) {
        container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No notifications found.</p>';
    }
}

async function updateNotificationBadge() {
    try {
        const res = await fetch('/api/student/notifications');
        const data = await res.json();
        if (data.success && data.notifications) {
            const count = data.notifications.length;
            const sBadge = document.getElementById('s-notif-count');
            const fBadge = document.getElementById('f-notif-count');
            if (sBadge) sBadge.textContent = count;
            if (fBadge) fBadge.textContent = count;
        }
    } catch (e) {}
}

function closeNotif() {
    const overlay = document.getElementById('notif-overlay');
    if (overlay) overlay.classList.remove('open');
}

function closeNotifOnOverlay(e) {
    if (e.target === document.getElementById('notif-overlay')) closeNotif();
}

document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
        closeModal();
        closeEditModal();
        closeNotif();
    }
});

/* ── ASSIGNMENT REPLACEMENT & EDIT ENGINE ── */
function openEditAssignmentModal() {
    if (!currentFacultyAssignment) {
        showToast('No assignment selected to edit.');
        return;
    }

    const a = currentFacultyAssignment;
    document.getElementById('edit-title').value = a.title || '';
    document.getElementById('edit-subject').value = a.subject || '';
    document.getElementById('edit-desc').value = a.description || '';
    document.getElementById('edit-marks').value = a.maximum_marks || 20;

    const deadlineInput = document.getElementById('edit-deadline');
    if (deadlineInput && a.deadline) {
        try {
            const dt = new Date(a.deadline);
            dt.setMinutes(dt.getMinutes() - dt.getTimezoneOffset());
            deadlineInput.value = dt.toISOString().slice(0, 16);
        } catch (err) {
            deadlineInput.value = '';
        }
    }

    document.getElementById('upload-fname-edit').style.display = 'none';
    document.getElementById('file-input-edit').value = '';
    document.getElementById('edit-assignment-modal').classList.add('open');
}

function closeEditModal() {
    const modal = document.getElementById('edit-assignment-modal');
    if (modal) modal.classList.remove('open');
}

function fileSelectedEdit(input) {
    const fname = input.files[0] ? input.files[0].name : '';
    const el = document.getElementById('upload-fname-edit');
    if (el && fname) {
        el.textContent = '📄 Replacement: ' + fname;
        el.style.display = 'block';
    }
}

async function handleEditAssignmentSubmit(e) {
    e.preventDefault();
    if (!currentFacultyAssignment || !currentFacultyAssignment.assignment_id) {
        showToast('Assignment ID missing.');
        return;
    }

    const formData = new FormData();
    formData.append('title', document.getElementById('edit-title').value.trim());
    formData.append('subject', document.getElementById('edit-subject').value.trim());
    formData.append('description', document.getElementById('edit-desc').value.trim());
    formData.append('maximum_marks', document.getElementById('edit-marks').value);
    formData.append('deadline', document.getElementById('edit-deadline').value);

    const fileInput = document.getElementById('file-input-edit');
    if (fileInput && fileInput.files && fileInput.files[0]) {
        formData.append('file', fileInput.files[0]);
    }

    showToast('Saving changes and replacing instruction file…');

    try {
        const res = await fetch(`/api/faculty/assignments/${currentFacultyAssignment.assignment_id}/update`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            closeEditModal();
            setTimeout(() => {
                loadFacultyAssignments();
                openFacultySubmissions(currentFacultyAssignment.assignment_id);
            }, 1200);
        } else {
            showToast(data.message || 'Update failed.');
        }
    } catch (err) {
        showToast('Error updating assignment.');
    }
}

function exportFacultyMarksCSV() {
    if (!currentFacultyAssignment || !currentFacultyAssignment.assignment_id) {
        showToast('No assignment selected to export.');
        return;
    }
    showToast('Exporting student marks sheet (CSV)…');
    window.open(`/api/faculty/assignments/${currentFacultyAssignment.assignment_id}/export-csv`, '_blank');
}

async function deleteFacultyAssignment() {
    if (!currentFacultyAssignment || !currentFacultyAssignment.assignment_id) {
        showToast('No assignment selected to delete.');
        return;
    }
    if (!confirm(`Are you sure you want to delete assignment "${currentFacultyAssignment.title}"? This cannot be undone.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/faculty/assignments/${currentFacultyAssignment.assignment_id}/delete`, {
            method: 'POST'
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message);
            setTimeout(() => {
                loadFacultyAssignments();
                showScreen('screen-faculty-dashboard');
            }, 1000);
        } else {
            showToast(data.message || 'Delete failed.');
        }
    } catch (e) {
        showToast('Error deleting assignment.');
    }
}
