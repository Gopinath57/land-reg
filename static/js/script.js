document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alerts after 6 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(al => {
    setTimeout(() => {
      al.style.opacity = '0';
      al.style.transition = 'opacity 0.4s ease';
      setTimeout(() => al.remove(), 400);
    }, 6000);
  });
});
