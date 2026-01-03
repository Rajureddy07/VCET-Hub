// ------------------- ADMIN CHECK -------------------
const isAdmin = localStorage.getItem("isAdmin") === "true";

let selectedSection = '';
let selectedBranch = '';
let selectedSemester = '';
let selectedSubject = '';
let selectedModule = '';
let historyStack = [];

// ------------------- NAVIGATION -------------------
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
  if (selectedSection === 'Notes') {
    subjects = ["Subject A", "Subject B", "Subject C"];
  } else if (selectedSection === 'Lab Manuals') {
    subjects = ["Physics Manual", "Chemistry Manual"];
  } else if (selectedSection === 'Question Papers') {
    subjects = ["Subject A", "Subject B"];
  } else if (selectedSection === 'Internal Papers') {
    subjects = ["Subject A", "Subject B"];
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

// ------------------- LOGIN / LOGOUT -------------------
function showLogin() {
  document.getElementById("loginModal").classList.remove("hidden");
}

function login() {
  const user = document.getElementById("username").value.trim();
  const pass = document.getElementById("password").value.trim();

  if (user === "vcet" && pass === "vcet123") {
    alert("✅ Login Successful");
    localStorage.setItem("isAdmin", "true");
    updateLoginUI(true);
    document.getElementById("loginModal").classList.add("hidden");
  } else {
    alert("❌ Invalid credentials");
  }
}

function logout() {
  localStorage.removeItem("isAdmin");
  updateLoginUI(false);
  alert("✅ Logged out successfully");
}

function updateLoginUI(isAdmin) {
  if (document.getElementById("loginBtn"))
    document.getElementById("loginBtn").classList.toggle("hidden", isAdmin);
  if (document.getElementById("logoutBtn"))
    document.getElementById("logoutBtn").classList.toggle("hidden", !isAdmin);
}

// ------------------- LOAD & DISPLAY UPLOADED FILES -------------------
async function loadUploadedFiles(branch, semester, subject, module) {
  const listDiv = document.getElementById("uploadedFiles");
  if (!listDiv) return;
  listDiv.innerHTML = "<p>Loading files...</p>";

  try {
    const res = await fetch(`http://127.0.0.1:5000/images?branch=${branch}&semester=${semester}&subject=${subject}&module=${module}`);
    const files = await res.json();
    listDiv.innerHTML = "";

    if (!files || files.length === 0) {
      listDiv.innerHTML = "<p>No files uploaded yet.</p>";
      return;
    }

    files.forEach(f => {
      const div = document.createElement("div");
      div.className = "uploaded-card";
      const filename = f.file.split("/").pop();

      // --- File Preview ---
      if (/\.(jpg|jpeg|png)$/i.test(filename)) {
        const img = document.createElement("img");
        img.src = `http://127.0.0.1:5000/${f.file}`;
        img.className = "preview-image";
        img.style.maxWidth = "100%";
        img.style.borderRadius = "10px";
        img.style.marginTop = "10px";
        div.appendChild(img);
      } else if (filename.endsWith(".pdf")) {
        const iframe = document.createElement("iframe");
        iframe.src = `http://127.0.0.1:5000/${f.file}`;
        iframe.className = "preview-pdf";
        iframe.style.width = "100%";
        iframe.style.height = "400px"; // ✅ full responsive height
        iframe.style.minHeight = "700px";
        iframe.style.borderRadius = "10px";
        iframe.style.border = "1px solid #333";
        iframe.style.marginTop = "10px";
        div.appendChild(iframe);
      } else if (filename.endsWith(".txt")) {
        const textEl = document.createElement("pre");
        textEl.textContent = f.content || filename;
        textEl.className = "preview-text";
        textEl.style.fontSize = "20px"; // ✅ increased font size
        textEl.style.lineHeight = "1.6";
        textEl.style.background = "#181818";
        textEl.style.padding = "15px";
        textEl.style.borderRadius = "10px";
        textEl.style.overflowX = "auto";
        div.appendChild(textEl);
      }

      // --- File Name ---
      const nameEl = document.createElement("p");
      nameEl.textContent = filename;
      nameEl.className = "uploaded-filename";
      div.appendChild(nameEl);

      // --- Download Button ---
      const downloadBtn = document.createElement("button");
      downloadBtn.textContent = "⬇️ Download";
      downloadBtn.className = "btn-download";
      downloadBtn.onclick = () => window.open(`http://127.0.0.1:5000/${f.file}`, "_blank");
      div.appendChild(downloadBtn);

      // --- Delete Button (Admin Only) ---
      if (isAdmin) {
        const delBtn = document.createElement("button");
        delBtn.textContent = "🗑 Delete";
        delBtn.className = "btn-delete";
        delBtn.onclick = async () => {
          if (!confirm("Are you sure you want to delete this file?")) return;
          await fetch("http://127.0.0.1:5000/delete", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ branch, semester, subject, module, filename })
          });
          alert("🗑 File deleted!");
          await loadUploadedFiles(branch, semester, subject, module);
        };
        div.appendChild(delBtn);
      }

      listDiv.appendChild(div);
    });
  } catch (err) {
    listDiv.innerHTML = "<p>⚠️ Error loading files.</p>";
    console.error(err);
  }
}

// ------------------- UPLOAD FILE (Admin Only) -------------------
async function uploadFile() {
  if (!isAdmin) return alert("Admin access only!");
  const fileInput = document.getElementById("fileInput");
  if (!fileInput || !fileInput.files[0]) return alert("Select a file to upload!");

  const urlParams = new URLSearchParams(window.location.search);
  const branch = urlParams.get("branch");
  const semester = urlParams.get("semester");
  const subject = urlParams.get("subject");
  const module = urlParams.get("module");

  const fd = new FormData();
  fd.append("file", fileInput.files[0]);
  fd.append("branch", branch);
  fd.append("semester", semester);
  fd.append("subject", subject);
  fd.append("module", module);

  const res = await fetch("http://127.0.0.1:5000/upload", { method: "POST", body: fd });
  const data = await res.json();

  if (data.message) {
    alert("✅ File uploaded successfully!");
    fileInput.value = "";
    await loadUploadedFiles(branch, semester, subject, module);
  } else {
    alert("⚠️ Upload failed!");
  }
}

// ------------------- AUTO LOAD FILES -------------------
document.addEventListener("DOMContentLoaded", () => {
  const params = new URLSearchParams(window.location.search);
  const branch = params.get("branch");
  const semester = params.get("semester");
  const subject = params.get("subject");
  const module = params.get("module");

  if (branch && semester && subject && module) {
    loadUploadedFiles(branch, semester, subject, module);
  }
});
