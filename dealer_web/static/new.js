// consumes sync_frm_clr from main.js
document.addEventListener('DOMContentLoaded', () => {
  const txn = document.getElementById('txn')

  txn.onclick = function() {
    if (txn.checked == true) {
      sync_frm_clr('BUY') } else {
      sync_frm_clr('SELL')
    }
  }

  if (txn.checked == true)
  sync_frm_clr('BUY')
}); 


const copyButton = document.getElementById('copyButton');

copyButton.addEventListener('click', () => {
  const sourceTable = document.querySelector('.mx-auto.table.table-compact');
  const targetTable = document.getElementById('basket_table');

  const rowsToCopy = Array.from(sourceTable.querySelectorAll('tr')).filter((row) => {
    const qtyInput = row.querySelector('input[name="qty"]');
    return qtyInput && Number(qtyInput.value) > 0;
  });

  rowsToCopy.forEach((row, index) => {
    const newRow = document.createElement('tr');

    const ptypeInputs = Array.from(document.querySelectorAll('input[name="ptype"]'));
    ptypeInputs.forEach((input) => {
      if (input.checked) {
       const title = input.getAttribute('data-title');
       newRow.innerHTML += `<td>${title}</td>`
      }
    });

    const otypeInputs = Array.from(document.querySelectorAll('input[name="otype"]'));
    otypeInputs.forEach((input) => {
      if (input.checked) {
        const title = input.getAttribute('data-title'); 
        newRow.innerHTML += `<td>${title}</td>`
      }
    });
    
    const qtyInput = row.querySelector('input[name="qty"]');
    const qty = qtyInput.value;
    newRow.innerHTML += `<td>${qty}</td>`;

    const clientNameInput = row.querySelector('input[name="client_name"]');
    const clientName = clientNameInput.value;
    newRow.innerHTML += `<td>${clientName}</td>`;

    const symbolInput = document.getElementById('symbol');
    newRow.innerHTML += `<td>${symbolInput.value}</td>`;

    const priceInput = document.getElementById('price');
    newRow.innerHTML += `<td>${priceInput.value}</td>`;

    const triggerInput = document.getElementById('trigger');
    newRow.innerHTML += `<td>${triggerInput.value}</td>`;

    const txnCheckbox = document.getElementById('txn');
    const txnValue = txnCheckbox.checked ? 'BUY' : 'SELL';
    newRow.innerHTML += `<td>${txnValue}</td>`;

    targetTable.appendChild(newRow);
  });
});

