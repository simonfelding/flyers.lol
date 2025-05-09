document.addEventListener('DOMContentLoaded', () => {
  const eventForm = document.getElementById('eventForm');
  const uploadIndicator = document.getElementById('uploadIndicator');
  const formMessage = document.getElementById('formMessage');
  const initialMessage = document.getElementById('initial-message');

  // Hide initial server-rendered message if user starts interacting
  if (eventForm) {
    eventForm.addEventListener('focusin', () => {
      if (initialMessage) {
        initialMessage.style.display = 'none';
      }
    });
  }

  if (eventForm) {
    eventForm.addEventListener('submit', async (event) => {
      event.preventDefault();

      // Hide previous messages and show animation
      if (initialMessage) initialMessage.style.display = 'none';
      formMessage.classList.add('hidden');
      formMessage.textContent = '';
      formMessage.className = 'mt-6 p-4 text-sm rounded-md hidden'; // Reset classes
      uploadIndicator.classList.remove('hidden');

      const form = event.target;
      const formData = new FormData(form);

      try {
        // Submit to admin-ui backend
        const response = await fetch('/submit-event', {
          method: 'POST',
          body: formData, // Send FormData directly, browser sets Content-Type
        });

        uploadIndicator.classList.add('hidden');
        const result = await response.json();

        if (result.success) {
          // Show success message (optional, as we redirect)
          // formMessage.textContent = `Event submitted successfully! Event ID: ${result.eventId}`;
          // formMessage.classList.remove('hidden');
          // formMessage.classList.add('bg-green-100', 'border', 'border-green-400', 'text-green-700');
          // eventForm.reset();
          window.location.href = '/?message=success&eventId=' + result.eventId; // Redirect to home with success message
        } else {
          formMessage.textContent = result.error || 'An unknown error occurred while submitting the event.';
          formMessage.classList.remove('hidden');
          formMessage.classList.add('bg-red-100', 'border', 'border-red-400', 'text-red-700');
        }
      } catch (error) {
        uploadIndicator.classList.add('hidden');
        formMessage.textContent = 'Network error or server unavailable. Please try again.';
        formMessage.classList.remove('hidden');
        formMessage.classList.add('bg-red-100', 'border', 'border-red-400', 'text-red-700');
        console.error('Error submitting form:', error);
      }
    });
  }
});