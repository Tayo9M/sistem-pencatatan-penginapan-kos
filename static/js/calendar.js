// This script handles calendar functionality

document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
});

function initializeCalendar() {
    // Highlight today's date
    const today = new Date();
    const todayDay = today.getDate();
    const todayMonth = today.getMonth() + 1;
    const todayYear = today.getFullYear();
    
    // Get current calendar month and year
    const calendarMonth = parseInt(document.getElementById('calendar').dataset.month);
    const calendarYear = parseInt(document.getElementById('calendar').dataset.year);
    
    // If current month and year match today, highlight today
    if (calendarMonth === todayMonth && calendarYear === todayYear) {
        const todayCell = document.querySelector(`.calendar-day[data-day="${todayDay}"]`);
        if (todayCell) {
            todayCell.classList.add('today');
        }
    }
    
    // Add click listeners to days with transactions
    document.querySelectorAll('.calendar-day[data-has-transactions="true"]').forEach(day => {
        day.addEventListener('click', function() {
            const dayNum = this.dataset.day;
            const transactions = JSON.parse(this.dataset.transactions || '[]');
            showTransactionDetails(dayNum, transactions);
        });
    });
    
    // Month navigation
    document.getElementById('prevMonth').addEventListener('click', function() {
        const prevMonth = parseInt(this.dataset.month);
        const prevYear = parseInt(this.dataset.year);
        window.location.href = `/calendar?month=${prevMonth}&year=${prevYear}`;
    });
    
    document.getElementById('nextMonth').addEventListener('click', function() {
        const nextMonth = parseInt(this.dataset.month);
        const nextYear = parseInt(this.dataset.year);
        window.location.href = `/calendar?month=${nextMonth}&year=${nextYear}`;
    });
}

function showTransactionDetails(day, transactions) {
    const modal = new bootstrap.Modal(document.getElementById('transactionModal'));
    const modalTitle = document.getElementById('transactionModalLabel');
    const modalBody = document.getElementById('transactionModalBody');
    
    modalTitle.textContent = `Transaksi Tanggal ${day}`;
    
    // Clear previous content
    modalBody.innerHTML = '';
    
    // Create table for transactions
    const table = document.createElement('table');
    table.className = 'table table-striped';
    table.innerHTML = `
        <thead>
            <tr>
                <th>Tipe</th>
                <th>Kategori</th>
                <th>Jumlah</th>
                <th>Deskripsi</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    
    const tbody = table.querySelector('tbody');
    
    transactions.forEach(transaction => {
        const row = document.createElement('tr');
        
        // Apply color based on transaction type
        if (transaction.type === 'income') {
            row.className = 'table-success';
        } else {
            row.className = 'table-warning';
        }
        
        row.innerHTML = `
            <td>${transaction.type === 'income' ? 'Pendapatan' : 'Pengeluaran'}</td>
            <td>${transaction.category}</td>
            <td>${formatRupiah(transaction.amount)}</td>
            <td>${transaction.description || '-'}</td>
        `;
        
        tbody.appendChild(row);
    });
    
    modalBody.appendChild(table);
    modal.show();
}

function formatRupiah(amount) {
    return 'Rp ' + parseInt(amount).toLocaleString('id-ID');
}
