// ==========================================================================
// Boba POS - Reports & DataGridView Analytics JS
// ==========================================================================

let currentPage = 1;
let currentLimit = 15;
let topDrinksChartInstance = null;
let categoryChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  setQuickDate('today');
  loadDashboardData();
  loadOrdersGrid();
});

// ==================== DASHBOARD SUMMARY & CHARTS ====================
async function loadDashboardData() {
  try {
    const res = await fetch('/api/reports/dashboard');
    const data = await res.json();
    if (!data.success) return;

    const s = data.summary;
    document.getElementById('kpiTodayUsd').innerText = `$${s.today_usd.toFixed(2)}`;
    document.getElementById('kpiTodayKhr').innerText = `${s.today_khr.toLocaleString()} ៛`;
    document.getElementById('kpiTodayOrders').innerText = s.today_orders;
    document.getElementById('kpiTodayCups').innerText = s.today_cups;
    document.getElementById('kpiMonthUsd').innerText = `$${s.month_usd.toFixed(2)}`;

    renderTopDrinksChart(data.top_drinks);
    renderCategoryChart(data.category_sales);
  } catch (e) {
    console.error('Failed to load dashboard:', e);
  }
}

function renderTopDrinksChart(drinks) {
  const ctx = document.getElementById('topDrinksChart').getContext('2d');
  if (topDrinksChartInstance) topDrinksChartInstance.destroy();

  const labels = drinks.map(d => d.product_name);
  const quantities = drinks.map(d => d.total_qty);

  topDrinksChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['មិនទាន់មានទិន្នន័យ'],
      datasets: [{
        label: 'ចំនួនកែវបានលក់ (Cups)',
        data: quantities.length ? quantities : [0],
        backgroundColor: [
          '#10b981', '#f59e0b', '#6366f1', '#ec4899', '#06b6d4'
        ],
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: { beginAtZero: true, ticks: { precision: 0 } }
      }
    }
  });
}

function renderCategoryChart(cats) {
  const ctx = document.getElementById('categorySalesChart').getContext('2d');
  if (categoryChartInstance) categoryChartInstance.destroy();

  const labels = cats.map(c => c.category_name);
  const revenues = cats.map(c => c.revenue);

  categoryChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels.length ? labels : ['មិនទាន់មានទិន្នន័យ'],
      datasets: [{
        data: revenues.length ? revenues : [1],
        backgroundColor: [
          '#059669', '#d97706', '#4f46e5', '#db2777', '#0891b2'
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right' }
      }
    }
  });
}

// ==================== DATAGRIDVIEW ====================
async function loadOrdersGrid() {
  const tbody = document.getElementById('ordersGridTbody');
  tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding:2rem; color:#94a3b8;"><i data-lucide="loader-2" class="spin"></i> កំពុងផ្ទុកទិន្នន័យ...</td></tr>`;
  lucide.createIcons();

  const startDate = document.getElementById('filterStartDate').value;
  const endDate = document.getElementById('filterEndDate').value;
  const cashier = document.getElementById('filterCashier').value;
  const payment = document.getElementById('filterPayment').value;
  const status = document.getElementById('filterStatus').value;
  const search = document.getElementById('gridSearchInput').value.trim();

  let url = `/api/reports/orders?page=${currentPage}&limit=${currentLimit}`;
  if (startDate) url += `&start_date=${startDate}`;
  if (endDate) url += `&end_date=${endDate}`;
  if (cashier) url += `&cashier_id=${cashier}`;
  if (payment) url += `&payment_method=${payment}`;
  if (status) url += `&status=${status}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) return;

    renderOrdersGridTable(data.orders);
    renderGridPagination(data.page, data.total_pages, data.total);
    
    document.getElementById('gridTotalRecords').innerText = data.total;
    document.getElementById('gridFilteredSumUsd').innerText = `$${data.filtered_total_usd.toFixed(2)}`;
    document.getElementById('gridFilteredSumKhr').innerText = `${data.filtered_total_khr.toLocaleString()} ៛`;
  } catch (e) {
    console.error('Failed to load orders grid:', e);
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; color:red; padding:1.5rem;">បរាជ័យក្នុងការទាញយកទិន្នន័យ</td></tr>`;
  }
}

function renderOrdersGridTable(orders) {
  const tbody = document.getElementById('ordersGridTbody');
  if (!orders || orders.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align:center; padding:2.5rem; color:#94a3b8;">
          <i data-lucide="inbox" style="width:36px;height:36px;margin-bottom:6px;"></i>
          <div>មិនមានទិន្នន័យវិក្កយបត្រដែលត្រូវនឹងលក្ខខណ្ឌស្វែងរកទេ</div>
        </td>
      </tr>
    `;
    lucide.createIcons();
    return;
  }

  tbody.innerHTML = orders.map(o => `
    <tr>
      <td><strong style="color:#0f172a;">${o.invoice_number}</strong></td>
      <td style="font-size:0.8rem; color:#64748b;">${o.created_at}</td>
      <td><strong>${o.cashier_name}</strong></td>
      <td>
        <span class="badge ${o.payment_method === 'cash' ? 'badge-info' : 'badge-warning'}" style="text-transform:uppercase;">
          ${o.payment_method}
        </span>
      </td>
      <td>$${o.subtotal_usd.toFixed(2)}</td>
      <td style="color:#b45309;">${o.discount_usd > 0 ? `-$${o.discount_usd.toFixed(2)}` : '$0.00'}</td>
      <td><strong style="font-size:0.95rem; color:#059669;">$${o.total_usd.toFixed(2)}</strong></td>
      <td style="font-size:0.85rem; font-weight:700; color:#475569;">${o.total_khr.toLocaleString()} ៛</td>
      <td>
        ${o.status === 'completed' 
          ? '<span class="badge badge-success">ជោគជ័យ</span>' 
          : '<span class="badge badge-danger">លុបចោល (Void)</span>'}
      </td>
      <td style="text-align:right; white-space:nowrap;">
        <button class="btn btn-secondary" style="padding:4px 8px; font-size:0.78rem;" onclick="viewReportReceipt(${o.id})" title="មើលវិក្កយបត្រ">
          <i data-lucide="receipt" style="width:14px;height:14px;"></i>
        </button>
        ${o.status === 'completed' ? `
          <button class="btn btn-danger" style="padding:4px 8px; font-size:0.78rem;" onclick="voidOrderAction(${o.id}, '${o.invoice_number}')" title="Void វិក្កយបត្រ & ត្រឡប់ស្តុក">
            <i data-lucide="slash" style="width:14px;height:14px;"></i> Void
          </button>
        ` : ''}
      </td>
    </tr>
  `).join('');

  lucide.createIcons();
}

function renderGridPagination(page, totalPages, totalRecords) {
  const container = document.getElementById('gridPaginationBtns');
  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }

  let html = `
    <button class="page-btn" ${page <= 1 ? 'disabled' : ''} onclick="goToGridPage(${page - 1})">« មុន</button>
  `;

  for (let p = Math.max(1, page - 2); p <= Math.min(totalPages, page + 2); p++) {
    html += `
      <button class="page-btn ${p === page ? 'active' : ''}" onclick="goToGridPage(${p})">${p}</button>
    `;
  }

  html += `
    <button class="page-btn" ${page >= totalPages ? 'disabled' : ''} onclick="goToGridPage(${page + 1})">បន្ទាប់ »</button>
  `;

  container.innerHTML = html;
}

function goToGridPage(p) {
  currentPage = p;
  loadOrdersGrid();
}

function changeGridLimit() {
  currentLimit = parseInt(document.getElementById('gridLimitSelect').value);
  currentPage = 1;
  loadOrdersGrid();
}

let gridSearchTimeout = null;
function handleGridSearch() {
  clearTimeout(gridSearchTimeout);
  gridSearchTimeout = setTimeout(() => {
    currentPage = 1;
    loadOrdersGrid();
  }, 300);
}

function applyFilters() {
  currentPage = 1;
  loadOrdersGrid();
}

function setQuickDate(type) {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, '0');
  const dd = String(now.getDate()).padStart(2, '0');
  const todayStr = `${yyyy}-${mm}-${dd}`;

  if (type === 'today') {
    document.getElementById('filterStartDate').value = todayStr;
    document.getElementById('filterEndDate').value = todayStr;
  } else if (type === 'month') {
    document.getElementById('filterStartDate').value = `${yyyy}-${mm}-01`;
    document.getElementById('filterEndDate').value = todayStr;
  }
  applyFilters();
}

function resetFilters() {
  document.getElementById('filterCashier').value = 'all';
  document.getElementById('filterPayment').value = 'all';
  document.getElementById('filterStatus').value = 'all';
  document.getElementById('gridSearchInput').value = '';
  setQuickDate('today');
}

// ==================== RECEIPT VIEW & VOID ====================
async function viewReportReceipt(orderId) {
  try {
    const res = await fetch(`/api/order/${orderId}/receipt`);
    const data = await res.json();
    if (data.success) {
      const o = data.receipt.order;
      const s = data.receipt.settings;
      const items = data.receipt.items;

      const html = `
        <div class="receipt-center">
          <div class="receipt-shop-name">${s.shop_name_km || 'ហាងតែគុជ ស្រស់ស្រាយ'}</div>
          <div class="receipt-shop-sub">${s.shop_name_en || 'Sros Sray Boba'}</div>
          <div style="font-size:11px; color:#475569;">${s.shop_address || 'ភ្នំពេញ'}</div>
          <div style="font-size:11px; color:#475569;">ទូរស័ព្ទ៖ ${s.shop_phone || '012 345 678'}</div>
        </div>
        <div class="receipt-divider"></div>
        <div class="receipt-info-row"><span>លេខវិក្កយបត្រ:</span><strong>${o.invoice_number}</strong></div>
        <div class="receipt-info-row"><span>កាលបរិច្ឆេទ:</span><span>${o.created_at}</span></div>
        <div class="receipt-info-row"><span>អ្នកគិតលុយ:</span><span>${o.cashier_name}</span></div>
        <div class="receipt-info-row"><span>ស្ថានភាព:</span><strong style="text-transform:uppercase;">${o.status}</strong></div>
        <div class="receipt-divider"></div>
        <table class="receipt-table">
          <thead><tr><th>មុខទំនិញ</th><th style="text-align:center;">ចំនួន</th><th style="text-align:right;">សរុប</th></tr></thead>
          <tbody>
            ${items.map(it => `
              <tr>
                <td>
                  <div style="font-weight:700;">${it.product_name} (${it.size})</div>
                  <div class="receipt-item-customs">ស្ករ ${it.sugar_level}, ${it.ice_level}</div>
                  ${it.toppings ? it.toppings.map(t=>`<div class="receipt-item-customs">+${t.topping_name}</div>`).join('') : ''}
                </td>
                <td style="text-align:center; font-weight:700;">${it.quantity}</td>
                <td style="text-align:right; font-weight:700;">$${it.item_total.toFixed(2)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
        <div class="receipt-divider"></div>
        <table class="receipt-totals-table">
          <tr class="receipt-grand-total"><td>សរុប (USD):</td><td style="text-align:right;">$${o.total_usd.toFixed(2)}</td></tr>
          <tr style="font-weight:700; color:#059669;"><td>សរុបជារៀល:</td><td style="text-align:right;">${o.total_khr.toLocaleString()} ៛</td></tr>
        </table>
      `;

      document.getElementById('reportReceiptContent').innerHTML = html;
      document.getElementById('receiptPrintArea').innerHTML = html;
      document.getElementById('reportReceiptModal').classList.add('show');
    }
  } catch (e) {
    alert('មិនអាចទាញយកវិក្កយបត្របានទេ!');
  }
}

async function voidOrderAction(orderId, invNumber) {
  if (confirm(`⚠️ តើអ្នកប្រាកដជាចង់ Void វិក្កយបត្រ "${invNumber}" មែនទេ?\nប្រព័ន្ធនឹងដកចំណូលចេញ និងត្រឡប់ស្តុកវត្ថុធាតុដើមវិញស្វ័យប្រវត្តិ!`)) {
    try {
      const res = await fetch(`/api/order/${orderId}/void`, { method: 'POST' });
      const result = await res.json();
      if (result.success) {
        alert(result.message);
        loadDashboardData();
        loadOrdersGrid();
      } else {
        alert(`កំហុស៖ ${result.error}`);
      }
    } catch (e) {
      alert('បរាជ័យក្នុងការ Void វិក្កយបត្រ!');
    }
  }
}

// ==================== EXPORT REPORTS ====================
function exportReport(format) {
  const startDate = document.getElementById('filterStartDate').value;
  const endDate = document.getElementById('filterEndDate').value;
  let url = `/api/reports/export/${format}?start_date=${startDate}&end_date=${endDate}`;
  window.open(url, '_blank');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('show');
}
