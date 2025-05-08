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
    eventForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      // Hide previous messages and show animation
      if (initialMessage) initialMessage.style.display = 'none';
      formMessage.classList.add('hidden');
      formMessage.textContent = '';
      formMessage.className = 'mt-6 p-4 text-sm rounded-md hidden'; // Reset classes
      uploadIndicator.classList.remove('hidden');

      const formData = new FormData(eventForm);
      const data = Object.fromEntries(formData.entries());

      try {
        const apiUrl = `${window.API_BASE_URL}/events`;
        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });

        uploadIndicator.classList.add('hidden');
        const result = await response.json();

        if (response.ok && result.success) {
          formMessage.textContent = `Event created successfully! Event ID: ${result.eventId}`;
          formMessage.classList.remove('hidden');
          formMessage.classList.add('bg-green-100', 'border', 'border-green-400', 'text-green-700');
          eventForm.reset(); // Clear the form
        } else {
          formMessage.textContent = result.message || 'An unknown error occurred.';
          formMessage.classList.remove('hidden');
          formMessage.classList.add('bg-red-100', 'border', 'border-red-400', 'text-red-700');
        }
      } catch (error) {
        uploadIndicator.classList.add('hidden');
        formMessage.textContent = 'Network error or server unavailable. Please try again.';
        formMessage.classList.remove('hidden');
        formMessage.classList.add('bg-red-100', 'border', 'border-red-400', 'text-red-700');
        console.error('Form submission error:', error);
      }
    });
  }
});