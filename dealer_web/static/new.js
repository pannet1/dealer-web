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
       newRow.innerHTML += `<td>
                          <input name="ptype[]" value=${title}>
                        </td>`
      }
    });
    const otypeInputs = Array.from(document.querySelectorAll('input[name="otype"]'));
    otypeInputs.forEach((input) => {
      if (input.checked) {
        const title = input.getAttribute('data-title'); 
        newRow.innerHTML += `<td>
                        <input name="otype[]" value=${title}>
                        </td>`
      }
    });
    const qtyInput = row.querySelector('input[name="qty"]');
    const qty = qtyInput.value;
    newRow.innerHTML += `<td>
                          <input name="quantity[]" value=${qty}>
                        </td>`;
    const clientNameInput = row.querySelector('input[name="client_name"]');
    const clientName = clientNameInput.value;
    newRow.innerHTML += `<td>
                          <input name="client_name[]" value=${clientName}>
                        </td>`;
    const symbolInput = document.getElementById('symbol');
    newRow.innerHTML += `<td>
                          <input name="tradingsymbol[]" value=${symbolInput.value}>
                        </td>`;
    const exchInput = document.getElementById('exchange');
    newRow.innerHTML += `<td>
                          <input name="exchange[]" value=${exchInput.value}>
                        </td>`;
    const tknInput = document.getElementById('token');
    newRow.innerHTML += `<td>
                          <input name="token[]" value=${tknInput.value}>
                        <td>`                 
    const priceInput = document.getElementById('price');
    newRow.innerHTML += `<td>
                          <input name="price" value=${priceInput.value}>
                        </td>`;

    const triggerInput = document.getElementById('trigger');
    newRow.innerHTML += `<td>
                          <input name="trigger" value=${triggerInput.value}>
                        </td>`;

    const txnCheckbox = document.getElementById('txn');
    const txnValue = txnCheckbox.checked ? 'BUY' : 'SELL';
    newRow.innerHTML += `<td>
                          <input name="transactiontype[]" value=${txnValue}>
                        </td>`;

    targetTable.appendChild(newRow);
  });
});

