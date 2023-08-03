function toggleStatus(spreadId, currentStatus) {
  const newStatus = currentStatus === 0 ? 1 : 0;

  fetch(`/toggle_status?id=${spreadId}&status=${newStatus}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
    .then(response => response.json())
    .then(data => {
      // Handle the response if needed
      console.log(data);
    })
    .catch(error => {
      // Handle errors if needed
      console.error('Error:', error);
    });
}






