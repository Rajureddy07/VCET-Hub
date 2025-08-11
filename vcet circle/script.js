const isAdmin = false; // Set to true for admin, false for users

let selectedSection = '';
let selectedBranch = '';
let selectedSemester = '';
let selectedSubject = '';
let selectedModule = '';
let historyStack = [];

function selectSection(section) {
  selectedSection = section;
  showPage('main-menu', 'branch-menu');
  document.getElementById('branch-title').textContent = `${section} - Select Branch`;
}

function selectBranch(branch) {
  selectedBranch = branch;
  showPage('branch-menu', 'semester-menu');
  document.getElementById('semester-title').textContent = `${selectedSection} - ${branch} - Select Semester`;
}

function selectSemester(sem) {
  selectedSemester = sem;
  showPage('semester-menu', 'subject-menu');
  document.getElementById('subject-title').textContent = `${selectedSection} - Semester ${sem} - Subjects`;

  const subjectList = document.getElementById('subject-list');
  subjectList.innerHTML = '';

  let subjects = [];

  if (selectedSection === 'Lab Manuals') {
    if (sem === 1) {
      subjects = ["Physics Manual", "Java Manual", "Mathematics Manual"];
    } else if (sem === 2) {
      subjects = ["Chemistry Manual", "C Manual", "Mathematics"];
    } else {
      subjects = ["Coming Soon"];
    }
  }

  if (selectedSection === 'Notes') {
    subjects = ["Subject A", "Subject B", "Subject C"]; // replace with real subjects
  }

  if (selectedSection === 'Question Papers') {
    subjects = ["Subject A", "Subject B", "Subject C"];
  }

  if (selectedSection === 'Internal Papers') {
    subjects = ["Subject A", "Subject B", "Subject C"];
  }

  subjects.forEach(subject => {
    const div = document.createElement('div');
    div.className = 'card';
    div.textContent = subject;
    div.onclick = () => openSubject(subject);
    subjectList.appendChild(div);
  });
}

function openSubject(subject) {
  selectedSubject = subject;

  // ✅ For Lab Manuals: skip module and go directly to preview/download
  if (selectedSection === 'Lab Manuals') {
    const url = `lab-view.html?branch=${selectedBranch}&semester=${selectedSemester}&subject=${encodeURIComponent(subject)}`;
    window.location.href = url;
    return;
  }

  // ✅ For Notes: show module selection step
  if (selectedSection === 'Notes') {
    showPage('subject-menu', 'module-menu');
    document.getElementById('module-title').textContent = `${subject} - Select Module`;

    const moduleList = document.getElementById('module-list');
    moduleList.innerHTML = '';

    for (let i = 1; i <= 5; i++) {
      const button = document.createElement('button');
      button.className = 'card';
      button.textContent = `Module ${i}`;
      button.onclick = () => openNotesModule(i);
      moduleList.appendChild(button);
    }
    return;
  }

  // ✅ For Question Papers: direct to question-view.html
  if (selectedSection === 'Question Papers') {
    const url = `question-view.html?branch=${selectedBranch}&semester=${selectedSemester}&subject=${encodeURIComponent(subject)}`;
    window.location.href = url;
    return;
  }

  // ✅ For Internal Papers: direct to internal-view.html
  if (selectedSection === 'Internal Papers') {
    const url = `internal-view.html?branch=${selectedBranch}&semester=${selectedSemester}&subject=${encodeURIComponent(subject)}`;
    window.location.href = url;
    return;
  }
}

function openNotesModule(moduleNum) {
  selectedModule = `Module ${moduleNum}`;
  const url = `module-view.html?branch=${selectedBranch}&semester=${selectedSemester}&subject=${encodeURIComponent(selectedSubject)}&module=${encodeURIComponent(selectedModule)}`;
  window.location.href = url;
}

function showPage(hideId, showId) {
  document.getElementById(hideId).classList.add('hidden');
  document.getElementById(showId).classList.remove('hidden');
  document.getElementById('back-btn').classList.remove('hidden');
  historyStack.push(hideId);
}

function goBack() {
  const current = document.querySelector('.card-container:not(.hidden)');
  const last = historyStack.pop();
  if (last) {
    current.classList.add('hidden');
    document.getElementById(last).classList.remove('hidden');
    if (historyStack.length === 0) {
      document.getElementById('back-btn').classList.add('hidden');
    }
  }
}
