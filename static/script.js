document.addEventListener("DOMContentLoaded", function () {
    const studentLoginForm = document.getElementById("studentLoginForm");
    const adminLoginForm = document.getElementById("adminLoginForm");
    const loginStatus = document.getElementById("loginStatus");

    // Student Login Handling
    if (studentLoginForm) {
        studentLoginForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const studentEmail = document.getElementById("studentEmail").value;

            if (validateEmail(studentEmail)) {
                localStorage.setItem("email", studentEmail);
                window.location.href = "/complaint"; // Redirect to complaint form
            } else {
                showError("Please enter a valid NITK email.");
            }
        });
    }

    // Admin Login Handling
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
                window.location.href = "/view_complaints"; // Redirect to admin page
            }
        });
    }

    function validateEmail(email) {
        return /^[a-zA-Z0-9._%+-]+@nitk\.edu\.in$/.test(email);
    }

    function validateAdminEmail(email) {
        return email === "admin@nitk.edu.in"; // Replace with actual admin validation if needed
    }

    function validateAdminPassword(password) {
        return password === "admin1234"; // Replace with actual hashed password check if needed
    }

    function showError(message) {
        if (loginStatus) {
            loginStatus.textContent = message;
            loginStatus.style.color = "red";
        }
    }

    // Handle Complaint Form Submission for Students
    const complaintForm = document.getElementById("complaintForm");
    if (complaintForm) {
        complaintForm.addEventListener("submit", function(event) {
            event.preventDefault();
            const email = localStorage.getItem("email");
            const name = document.getElementById("name").value;
            const rollNumber = document.getElementById("rollNumber").value;
            const mess = document.getElementById("mess").value;
            const date = document.getElementById("date").value;
            const description = document.getElementById("description").value;

            if (name && rollNumber && mess && date && description) {
                fetch("/submit", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, name, rollNumber, mess, date, description })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.message) {
                        document.getElementById("status").textContent = `Complaint Submitted Successfully. Category: ${data.category}`;
                        document.getElementById("complaintId").textContent = `Complaint ID: ${data.complaint_id}`;
                        document.getElementById("status").style.color = "green";
                    } else if (data.error) {
                        document.getElementById("status").textContent = `Error: ${data.error}`;
                        document.getElementById("status").style.color = "red";
                    }
                })
                .catch(error => {
                    document.getElementById("status").textContent = "An error occurred while submitting your complaint.";
                    document.getElementById("status").style.color = "red";
                });
            } else {
                document.getElementById("status").textContent = "All fields are required.";
                document.getElementById("status").style.color = "red";
            }
        });
    }

    // Fetch Complaints for Admin
    const fetchComplaintsButton = document.getElementById("fetchComplaints");
    if (fetchComplaintsButton) {
        fetchComplaintsButton.addEventListener("click", function () {
            const category = document.getElementById("category").value;
            fetch(`/complaints/${encodeURIComponent(category)}`)
                .then(response => response.json())
                .then(data => {
                    const complaintListDiv = document.getElementById("complaintList");
                    complaintListDiv.innerHTML = ""; // Clear previous results

                    if (data.complaints && data.complaints.length > 0) {
                        data.complaints.forEach(complaint => {
                            const complaintItem = document.createElement("p");
                            complaintItem.textContent = `ID: ${complaint[0]}, Name: ${complaint[1]}, Mess: ${complaint[3]}, Date: ${complaint[4]}, Status: ${complaint[6]}`;
                            complaintListDiv.appendChild(complaintItem);
                        });
                    } else {
                        complaintListDiv.textContent = "No complaints found for this category.";
                    }
                })
                .catch(error => {
                    console.error("Error fetching complaints:", error);
                    document.getElementById("complaintList").textContent = "Error fetching complaints.";
                });
        });
    }

    // Check Complaint Status for Students
    const checkStatusButton = document.getElementById("checkStatusButton");
    if (checkStatusButton) {
        checkStatusButton.addEventListener("click", function () {
            const complaintId = document.getElementById("complaintIdInput").value;
            fetch(`/status/${complaintId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById("complaintStatus").textContent = data.status ? `Complaint Status: ${data.status}` : `Error: ${data.error}`;
            })
            .catch(error => {
                document.getElementById("complaintStatus").textContent = "Error retrieving complaint status.";
            });
        });
    }
});
