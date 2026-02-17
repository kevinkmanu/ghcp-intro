document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
        // remember current selection so we can restore it after re-render
        const previousSelection = activitySelect.value;

        const response = await fetch("/activities");
        const activities = await response.json();

        // Clear loading message
        activitiesList.innerHTML = "";

        // Populate activities list
        displayActivities(activities);

        // restore previous selection if it's still available
        if (previousSelection) {
          const exists = Array.from(activitySelect.options).some(o => o.value === previousSelection);
          if (exists) activitySelect.value = previousSelection;
        }
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Function to display activities
  function displayActivities(activities) {
    const activitiesList = document.getElementById("activities-list");
    const activitySelect = document.getElementById("activity");

    // Clear existing content
    activitiesList.innerHTML = "";
    activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

    // Display each activity
    for (const [name, details] of Object.entries(activities)) {
      // Create activity card
      const card = document.createElement("div");
      card.className = "activity-card";

      const participantCount = details.participants.length;
      const participantsHTML = participantCount > 0
        ? `<ul class="participants-list">
             ${details.participants.map(email => `<li>${email}</li>`).join('')}
            </ul>`
        : `<p class="no-participants">No participants yet</p>`;

      card.innerHTML = `
        <h4>${name}</h4>
        <p><strong>Description:</strong> ${details.description}</p>
        <p><strong>Schedule:</strong> ${details.schedule}</p>
        <p><strong>Capacity:</strong> ${participantCount}/${details.max_participants} students</p>
        <div class="participants-section">
          <p><strong>Participants (${participantCount}):</strong></p>
          ${participantsHTML}
        </div>
      `;

      activitiesList.appendChild(card);

      // Add option to select dropdown
      const option = document.createElement("option");
      option.value = name;
      option.textContent = name;
      activitySelect.appendChild(option);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.classList.remove("success", "error", "info");
        messageDiv.classList.add("message", "success");

        // Clear only the email field so the selected activity remains
        const emailInput = document.getElementById("email");
        if (emailInput) emailInput.value = "";

        // Refresh activities so the participants list updates immediately
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.classList.remove("success", "error", "info");
        messageDiv.classList.add("message", "error");
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
