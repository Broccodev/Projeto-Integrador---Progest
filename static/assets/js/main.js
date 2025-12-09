document.addEventListener('DOMContentLoaded', () => {
  const forms = document.querySelectorAll('form');
  forms.forEach((form) => {
    form.addEventListener('submit', () => {
      // noop: submissão é tratada pelo servidor
    });
  });
});
document.querySelectorAll('.donut-chart').forEach(chart => {
    const value = chart.dataset.value;
    const max = chart.dataset.max;
    const percent = Math.min((value / max) * 100, 100);
    chart.style.setProperty('--p', percent);
});