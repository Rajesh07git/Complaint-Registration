document.addEventListener("DOMContentLoaded", function () {
  // Mobile menu toggle
  const hamburger = document.querySelector(".hamburger");
  const navLinks = document.querySelector(".nav-links");
  
  if (hamburger) {
    hamburger.addEventListener("click", function() {
      navLinks.classList.toggle("active");
    });
  }

  // Student Login Handling
  const studentLoginForm = document.getElementById("studentLoginForm");
  if (studentLoginForm) {
    studentLoginForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const studentEmail = document.getElementById("studentEmail").value;

      if (validateEmail(studentEmail)) {
        localStorage.setItem("email", studentEmail);
        window.location.href = "/student_dashboard"; // Redirect to student dashboard
      } else {
        showError("Please enter a valid NITK email.");
      }
    });
  }

  // Admin Login Handling
  const adminLoginForm = document.getElementById("adminLoginForm");
  if (adminLoginForm) {
    adminLoginForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const adminEmail = document.getElementById("adminEmail").value;
      const adminPassword = document.getElementById("adminPassword").value;

      if (!validateAdminEmail(adminEmail)) {
        showError("Please enter a valid admin email.");
      } else if (!validateAdminPassword(adminPassword)) {
        showError("Incorrect password. Please try again.");
      } else {
        localStorage.setItem("adminEmail", adminEmail);
        window.location.href = "/admin_dashboard"; // Redirect to admin dashboard
      }
    });
  }

  function validateEmail(email) {
    return /^[a-z]+\.[0-9]{3}[a-z]{2}[0-9]{3}@nitk\.edu\.in$/.test(email);
  }

  function validateAdminEmail(email) {
    return email === "admin@nitk.edu.in"; // Allow admin and category-specific admins
  }

  function validateAdminPassword(password) {
    return password === "admin@1234"; // In production, this should be a secure validation
  }

  function showError(message) {
    const loginStatus = document.getElementById("loginStatus");
    if (loginStatus) {
      loginStatus.textContent = message;
      loginStatus.style.color = "red";
    }
  }

  // Handle Complaint Form Submission for Students
  const complaintForm = document.getElementById("complaintForm");
  if (complaintForm) {
    complaintForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const email = localStorage.getItem("email");
      const name = document.getElementById("name").value;
      const rollNumber = document.getElementById("rollNumber").value;
      const mess = document.getElementById("mess").value;
      const date = document.getElementById("date").value;
      const description = document.getElementById("description").value;

      if (!email) {
        window.location.href = "/student_login"; // Redirect to login if not logged in
        return;
      }

      if (name && rollNumber && mess && date && description) {
        fetch("/submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email,
            name,
            rollNumber,
            mess,
            date,
            description,
          }),
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.message) {
              document.getElementById(
                "status"
              ).textContent = `Complaint Submitted Successfully! Category: ${data.category}`;
              document.getElementById(
                "complaintId"
              ).textContent = `Your Complaint ID: ${data.complaint_id} (Save this ID to check status later)`;
              document.getElementById("status").style.color = "green";
              
              // Reset form
              complaintForm.reset();
            } else if (data.error) {
              document.getElementById(
                "status"
              ).textContent = `Error: ${data.error}`;
              document.getElementById("status").style.color = "red";
            }
          })
          .catch((error) => {
            document.getElementById("status").textContent =
              "An error occurred while submitting your complaint.";
            document.getElementById("status").style.color = "red";
          });
      } else {
        document.getElementById("status").textContent =
          "All fields are required.";
        document.getElementById("status").style.color = "red";
      }
    });
  }

  // Check Complaint Status for Students
  const checkStatusButton = document.getElementById("checkStatusButton");
  if (checkStatusButton) {
    checkStatusButton.addEventListener("click", function () {
      const complaintId = document.getElementById("complaintIdInput").value;
      if (!complaintId) {
        document.getElementById("complaintStatus").textContent = "Please enter a complaint ID";
        document.getElementById("complaintStatus").style.color = "red";
        return;
      }
      
      fetch(`/status/${complaintId}`)
        .then((response) => response.json())
        .then((data) => {
          if (data.status) {
            document.getElementById("complaintStatus").textContent = `Complaint Status: ${data.status}`;
            document.getElementById("complaintStatus").style.color = getStatusColor(data.status);
          } else {
            document.getElementById("complaintStatus").textContent = `Error: ${data.error || "Complaint not found"}`;
            document.getElementById("complaintStatus").style.color = "red";
          }
        })
        .catch((error) => {
          document.getElementById("complaintStatus").textContent =
            "Error retrieving complaint status.";
          document.getElementById("complaintStatus").style.color = "red";
        });
    });
  }

  // Fetch Complaints for Admin with automatic URL parameter handling
  const fetchComplaintsButton = document.getElementById("fetchComplaints");
  if (fetchComplaintsButton) {
    // Check if URL has a category parameter
    const urlParams = new URLSearchParams(window.location.search);
    const categoryParam = urlParams.get('category');
    
    // Set the dropdown to the category from URL if present
    if (categoryParam) {
      const categorySelect = document.getElementById("category");
      if (categorySelect) {
        for (let i = 0; i < categorySelect.options.length; i++) {
          if (categorySelect.options[i].value === categoryParam) {
            categorySelect.selectedIndex = i;
            break;
          }
        }
        // Trigger the fetch automatically
        loadComplaints(categoryParam);
      }
    }
    
    fetchComplaintsButton.addEventListener("click", function () {
      const category = document.getElementById("category").value;
      loadComplaints(category);
    });
  }

  // Function to load complaints
  function loadComplaints(category) {
    const complaintListDiv = document.getElementById("complaintList");
    if (!complaintListDiv) return;
    
    complaintListDiv.innerHTML = '<p style="text-align: center;">Loading complaints...</p>';
    
    fetch(`/complaints/${encodeURIComponent(category)}`)
      .then((response) => response.json())
      .then((data) => {
        complaintListDiv.innerHTML = ""; // Clear loading message

        if (data.complaints && data.complaints.length > 0) {
          data.complaints.forEach((complaint) => {
            const div = document.createElement("div");
            div.classList.add("complaint-item");
            div.setAttribute("data-id", complaint[0]);

            const statusColor = getStatusColorClass(complaint[7]);
            const statusBadge = `<span class="status-badge ${statusColor}">${complaint[7]}</span>`;

            div.innerHTML = `
              <div>
                <p><strong>ID:</strong> ${complaint[0]} | <strong>Name:</strong> ${complaint[1]} | <strong>Mess:</strong> ${complaint[3]}</p>
                <p><strong>Date:</strong> ${complaint[4]} | <strong>Status:</strong> ${statusBadge}</p>
                <p><strong>Description:</strong> ${complaint[6]}</p>
              </div>
              <div class="complaint-actions">
                ${complaint[7] !== "Completed" ? 
                  `<button class="update-status-btn" data-id="${complaint[0]}">Update Status</button>` : 
                  `<span class="completed-badge">Resolved</span>`}
              </div>
            `;
            complaintListDiv.appendChild(div);
          });
          
          // Add event listeners to the newly created update buttons
          addUpdateButtonListeners();
        } else {
          complaintListDiv.innerHTML = `
            <div class="no-complaints">
              <i class="fas fa-search" style="font-size: 2rem; color: var(--gray); margin-bottom: 1rem;"></i>
              <p>No complaints found for ${category} category.</p>
            </div>
          `;
        }
      })
      .catch((error) => {
        console.error("Error fetching complaints:", error);
        complaintListDiv.innerHTML = `
          <div class="error-message">
            <i class="fas fa-exclamation-circle" style="font-size: 2rem; color: var(--danger); margin-bottom: 1rem;"></i>
            <p>Error fetching complaints. Please try again later.</p>
          </div>
        `;
      });
  }

  // Add event listeners to update status buttons
  function addUpdateButtonListeners() {
    const updateButtons = document.querySelectorAll('.update-status-btn');
    updateButtons.forEach(button => {
      button.addEventListener('click', function() {
        const complaintId = this.getAttribute('data-id');
        updateComplaintStatus(complaintId);
      });
    });
  }

  function updateComplaintStatus(complaintId) {
    const statusOptions = ['In Progress', 'Completed'];
    const statusSelect = document.createElement('select');
    statusOptions.forEach(option => {
        const optElement = document.createElement('option');
        optElement.value = option;
        optElement.textContent = option;
        statusSelect.appendChild(optElement);
    });
    
    // Create a dialog for status update
    const dialog = document.createElement('div');
    dialog.className = 'status-update-dialog';
    dialog.innerHTML = `
        <h3>Update Complaint Status</h3>
        <p>Select the new status for complaint #${complaintId}:</p>
        <div class="status-select-container"></div>
        <div class="dialog-actions">
            <button class="cancel-btn">Cancel</button>
            <button class="confirm-btn">Update</button>
        </div>
    `;
    
    // Add the select element to the dialog
    dialog.querySelector('.status-select-container').appendChild(statusSelect);
    
    // Create overlay background
    const overlay = document.createElement('div');
    overlay.className = 'status-update-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.right = '0';
    overlay.style.bottom = '0';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    overlay.style.zIndex = '999';
    
    // Add the dialog and overlay to the document
    document.body.appendChild(overlay);
    document.body.appendChild(dialog);
    
    // Add event listeners for buttons
    dialog.querySelector('.cancel-btn').addEventListener('click', function() {
        removeDialogAndOverlay();
    });
    
    function removeDialogAndOverlay() {
        if (document.body.contains(dialog)) {
            document.body.removeChild(dialog);
        }
        if (document.body.contains(overlay)) {
            document.body.removeChild(overlay);
        }
    }
    
    dialog.querySelector('.confirm-btn').addEventListener('click', function() {
        const newStatus = statusSelect.value;
        
        fetch(`/update_status/${complaintId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the dialog and overlay
                removeDialogAndOverlay();
                
                // Find the complaint item and update it
                const complaintItem = document.querySelector(`[data-id="${complaintId}"]`);
                if (complaintItem) {
                    const statusBadge = complaintItem.querySelector('.status-badge');
                    if (statusBadge) {
                        statusBadge.textContent = newStatus;
                        statusBadge.className = `status-badge ${getStatusColorClass(newStatus)}`;
                    }
                    
                    // If completed, replace the button with a completed badge
                    if (newStatus === 'Completed') {
                        const actionsDiv = complaintItem.querySelector('.complaint-actions');
                        if (actionsDiv) {
                            actionsDiv.innerHTML = '<span class="completed-badge">Resolved</span>';
                        }
                    }
                }
            } else {
                alert('Failed to update status: ' + (data.error || 'Unknown error'));
                removeDialogAndOverlay(); // Make sure to remove even on error
            }
        })
        .catch(error => {
            console.error('Error updating status:', error);
            alert('An error occurred while updating the status.');
            removeDialogAndOverlay(); // Make sure to remove even on error
        });
    });
    
    // Style the dialog to appear as a modal
    dialog.style.position = 'fixed';
    dialog.style.top = '50%';
    dialog.style.left = '50%';
    dialog.style.transform = 'translate(-50%, -50%)';
    dialog.style.padding = '2rem';
    dialog.style.backgroundColor = 'white';
    dialog.style.borderRadius = '10px';
    dialog.style.boxShadow = '0 0 20px rgba(0, 0, 0, 0.3)';
    dialog.style.zIndex = '1000';
  }
  
  // If we're on the admin dashboard, refresh the stats
if (window.location.pathname === '/admin_dashboard') {
  loadDashboardStats();
}

  // Function to get status color class
  function getStatusColorClass(status) {
    if (status === 'Completed') return 'status-completed';
    if (status === 'In Progress') return 'status-progress';
    return 'status-pending';
  }

  // Function to get status color
  function getStatusColor(status) {
    if (status === 'Completed') return 'var(--success)';
    if (status === 'In Progress') return 'var(--primary)';
    return 'var(--warning)';
  }

  // Voice-to-Text using Web Speech API
  const startRecordingBtn = document.getElementById("startRecording");
  const recordingStatus = document.getElementById("recordingStatus");
  const descriptionField = document.getElementById("description");

  if (startRecordingBtn && (window.SpeechRecognition || window.webkitSpeechRecognition)) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-IN";

    startRecordingBtn.addEventListener("click", () => {
      recognition.start();
      recordingStatus.textContent = "Listening...";
      recordingStatus.style.color = "var(--primary)";
      startRecordingBtn.disabled = true;
    });

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      descriptionField.value += transcript + " "; // Append to existing text with space
      recordingStatus.textContent = "Transcription complete ✅";
      recordingStatus.style.color = "var(--success)";
      startRecordingBtn.disabled = false;
    };

    recognition.onerror = (event) => {
      recordingStatus.textContent = `Error: ${event.error}`;
      recordingStatus.style.color = "var(--danger)";
      startRecordingBtn.disabled = false;
    };

    recognition.onend = () => {
      if (recordingStatus.style.color !== "var(--success)") {
        recordingStatus.textContent = "Listening ended. Click to speak again.";
        recordingStatus.style.color = "var(--gray)";
      }
      startRecordingBtn.disabled = false;
    };
  } else {
    if (startRecordingBtn) {
      startRecordingBtn.disabled = true;
      startRecordingBtn.textContent = "Voice not supported in this browser";
      startRecordingBtn.style.backgroundColor = "var(--gray)";
    }
  }

  // Set today's date as the default for date input
  const dateInput = document.getElementById("date");
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.value = today;
    dateInput.max = today; // Prevent future dates
  }
});