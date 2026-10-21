const selectAll = document.getElementById('select-all-tests');
const selections = Array.from(document.querySelectorAll('input[name="tests"]'));
const updateApprovalButton = () => document.querySelectorAll('[data-requires-selection]').forEach(button=>{button.disabled=!selections.some(box=>box.checked)});
updateApprovalButton();
selections.forEach(box=>box.addEventListener('change',updateApprovalButton));
if (selectAll) {
  selectAll.addEventListener('change', () => {selections.forEach(box => { box.checked = selectAll.checked; });updateApprovalButton();});
  selections.forEach(box => box.addEventListener('change', () => {
    selectAll.checked = selections.every(item => item.checked);
    selectAll.indeterminate = selections.some(item => item.checked) && !selectAll.checked;
  }));
}
const progress = document.querySelector('[data-workflow-poll]');
if (progress) {
  const poll = async () => {
    try {
      const response = await fetch(progress.dataset.workflowPoll, {cache: 'no-store'});
      if (!response.ok) throw new Error('Status unavailable');
      const result = await response.json();
      if (!['generation_queued', 'generating', 'code_generating', 'queued', 'running'].includes(result.status)) {
        window.location.reload();
        return;
      }
      if (result.status === 'running') document.getElementById('run-progress').textContent = `${result.completed} of ${result.selected} selected tests finished. The remaining tests are running or being prepared.`;
    } catch {
      document.getElementById('run-progress').textContent = 'Cannot reach the application. Check that the server is still running, then refresh this page.';
    }
    window.setTimeout(poll, 2500);
  };
  window.setTimeout(poll, 2000);
}
