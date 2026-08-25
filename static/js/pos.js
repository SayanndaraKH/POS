// ==========================================================================
// Boba POS - Point of Sale Front-End Logic
// ==========================================================================

let allProducts = [];
let activeCategory = 'all';
let cart = [];
let currentProduct = null;
let currentSize = null;
let customQty = 1;
let activePaymentMethod = 'cash';
let exchangeRate = 4100;

document.addEventListener('DOMContentLoaded', () => {
  const rateElem = document.getElementById('currentExchangeRate');
  if (rateElem) {
    exchangeRate = parseFloat(rateElem.innerText) || 4100;
  }
  loadProducts();
});

// 1. Fetch Products
async function loadProducts(catId = 'all', search = '') {
  try {
    let url = `/api/pos/products?category_id=${catId}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    
    const res = await fetch(url);
    const data = await res.json();
    if (data.success) {
      allProducts = data.products;
      renderProductsGrid(allProducts);
    }
  } catch (err) {
    console.error('Failed to load products:', err);
  }
}

// 2. Render Products Grid
function renderProductsGrid(products) {
  const grid = document.getElementById('productsGrid');
  if (!grid) return;

  if (products.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align:center; padding:3rem; color:#94a3b8;">
        <i data-lucide="coffee" style="width:40px;height:40px;margin-bottom:8px;"></i>
        <div>មិនមានភេសជ្ជៈដែលត្រូវនឹងការស្វែងរកទេ</div>
      </div>
    `;
    lucide.createIcons();
    return;
  }

  grid.innerHTML = products.map(p => {
    const priceKhr = Math.round(p.base_price * exchangeRate).toLocaleString();
    return `
      <div class="product-card" onclick="openCustomModal(${p.id})">
        <div class="product-img-wrap">
          <img src="${p.image_url || '/static/images/brown_sugar_boba.svg'}" alt="${p.name_km}" class="product-img">
        </div>
        <div class="product-code">${p.code || 'DRINK'}</div>
        <div class="product-name-km">${p.name_km}</div>
        <div class="product-name-en">${p.name_en || ''}</div>
        <div class="product-price-row">
          <span class="product-price-usd">$${p.base_price.toFixed(2)}</span>
          <span class="product-price-khr">${priceKhr} ៛</span>
        </div>
      </div>
    `;
  }).join('');

  lucide.createIcons();
}

// Category filter
function selectCategory(catId, btn) {
  activeCategory = catId;
  document.querySelectorAll('.category-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const searchVal = document.getElementById('drinkSearchInput').value.trim();
  loadProducts(catId, searchVal);
}

// Search bar input
let searchTimeout = null;
function handleSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    const searchVal = document.getElementById('drinkSearchInput').value.trim();
    loadProducts(activeCategory, searchVal);
  }, 250);
}

// ==================== CUSTOMIZATION MODAL ====================
function openCustomModal(productId) {
  currentProduct = allProducts.find(p => p.id === productId);
  if (!currentProduct) return;

  document.getElementById('customDrinkTitleKm').innerText = currentProduct.name_km;
  document.getElementById('customDrinkTitleEn').innerText = currentProduct.name_en || '';
  document.getElementById('customItemNotes').value = '';
  customQty = 1;
  document.getElementById('customQtyDisplay').innerText = customQty;

  // Reset radio buttons
  document.getElementById('s100').checked = true;
  document.getElementById('i100').checked = true;

  // Reset checkboxes
  document.querySelectorAll('.topping-checkbox-card input').forEach(cb => cb.checked = false);

  // Render sizes
  const sizesGrid = document.getElementById('sizeOptionsGrid');
  if (currentProduct.sizes && currentProduct.sizes.length > 0) {
    sizesGrid.innerHTML = currentProduct.sizes.map((s, idx) => `
      <div class="opt-radio-pill">
        <input type="radio" name="size" id="size_${s.size_code}" value="${s.size_code}" data-extra="${s.extra_price}" data-name="${s.size_name_km}" ${idx === 0 ? 'checked' : ''} onchange="recalculateCustomTotal()">
        <label for="size_${s.size_code}">
          ${s.size_name_km} ${s.extra_price > 0 ? `(+$${s.extra_price.toFixed(2)})` : ''}
        </label>
      </div>
    `).join('');
  } else {
    sizesGrid.innerHTML = `
      <div class="opt-radio-pill">
        <input type="radio" name="size" id="size_M" value="M" data-extra="0" data-name="កែវធម្មតា (M)" checked onchange="recalculateCustomTotal()">
        <label for="size_M">កែវធម្មតា (M)</label>
      </div>
    `;
  }

  recalculateCustomTotal();
  document.getElementById('customModal').classList.add('show');
}

function closeCustomModal() {
  document.getElementById('customModal').classList.remove('show');
}

function changeCustomQty(delta) {
  customQty = Math.max(1, customQty + delta);
  document.getElementById('customQtyDisplay').innerText = customQty;
  recalculateCustomTotal();
}

function recalculateCustomTotal() {
  if (!currentProduct) return;
  
  let unitPrice = currentProduct.base_price;
  
  // Size extra
  const selectedSize = document.querySelector('input[name="size"]:checked');
  if (selectedSize) {
    unitPrice += parseFloat(selectedSize.dataset.extra || 0);
  }

  // Toppings extra
  let topTotal = 0;
  document.querySelectorAll('.topping-checkbox-card input:checked').forEach(cb => {
    topTotal += parseFloat(cb.dataset.price || 0);
  });

  const total = (unitPrice + topTotal) * customQty;
  document.getElementById('customTotalDisplay').innerText = `$${total.toFixed(2)}`;
}

function confirmAddToCart() {
  if (!currentProduct) return;

  const selectedSize = document.querySelector('input[name="size"]:checked');
  const sizeCode = selectedSize ? selectedSize.value : 'M';
  const sizeName = selectedSize ? selectedSize.dataset.name : 'M';
  const sizeExtra = selectedSize ? parseFloat(selectedSize.dataset.extra || 0) : 0;

  const sugar = document.querySelector('input[name="sugar"]:checked').value;
  const ice = document.querySelector('input[name="ice"]:checked').value;
  const notes = document.getElementById('customItemNotes').value.trim();

  const selectedToppings = [];
  document.querySelectorAll('.topping-checkbox-card input:checked').forEach(cb => {
    selectedToppings.push({
      id: parseInt(cb.value),
      name_km: cb.dataset.name,
      price: parseFloat(cb.dataset.price || 0)
    });
  });

  const itemUnitPrice = currentProduct.base_price + sizeExtra;

  // Build cart item object
  const cartItem = {
    cart_item_id: Date.now() + Math.random(),
    product_id: currentProduct.id,
    product_name: currentProduct.name_km,
    product_name_en: currentProduct.name_en,
    code: currentProduct.code,
    size: sizeCode,
    size_name: sizeName,
    sugar_level: sugar,
    ice_level: ice,
    toppings: selectedToppings,
    unit_price: itemUnitPrice,
    quantity: customQty,
    notes: notes
  };

  // Check if identical item already in cart
  const existingIdx = cart.findIndex(it => 
    it.product_id === cartItem.product_id &&
    it.size === cartItem.size &&
    it.sugar_level === cartItem.sugar_level &&
    it.ice_level === cartItem.ice_level &&
    it.notes === cartItem.notes &&
    JSON.stringify(it.toppings.map(t=>t.id).sort()) === JSON.stringify(cartItem.toppings.map(t=>t.id).sort())
  );

  if (existingIdx > -1) {
    cart[existingIdx].quantity += cartItem.quantity;
  } else {
    cart.push(cartItem);
  }

  playBeep('add');
  closeCustomModal();
  renderCart();
}

// ==================== CART MANAGEMENT ====================
function renderCart() {
  const list = document.getElementById('cartItemsList');
  const countBadge = document.getElementById('cartCountBadge');
  const btnPay = document.getElementById('btnPay');

  if (!list) return;

  const totalItemCount = cart.reduce((sum, it) => sum + it.quantity, 0);
  countBadge.innerText = totalItemCount;

  if (cart.length === 0) {
    list.innerHTML = `
      <div class="cart-empty-state">
        <i data-lucide="cup-soda"></i>
        <div style="font-weight:700; font-size:0.95rem; color:#64748b;">មិនទាន់មានភេសជ្ជៈក្នុងកន្ត្រកទេ</div>
        <div style="font-size:0.8rem; color:#94a3b8;">សូមចុចលើភេសជ្ជៈខាងឆ្វេងដើម្បីជ្រើសរើស</div>
      </div>
    `;
    btnPay.disabled = true;
    updateCartTotals();
    lucide.createIcons();
    return;
  }

  btnPay.disabled = false;
  list.innerHTML = cart.map(item => {
    const topPrice = item.toppings.reduce((s, t) => s + t.price, 0);
    const lineTotal = (item.unit_price + topPrice) * item.quantity;
    const toppingsDisplay = item.toppings.map(t => `<span class="custom-tag">+${t.name_km}</span>`).join(' ');

    return `
      <div class="cart-item-card">
        <div class="cart-item-header">
          <div>
            <div class="cart-item-name">${item.product_name}</div>
            <div class="cart-item-tags" style="margin-top:2px;">
              <span class="custom-tag size-tag">${item.size_name || item.size}</span>
              <span class="custom-tag">ស្ករ ${item.sugar_level}</span>
              <span class="custom-tag">${item.ice_level}</span>
              ${toppingsDisplay}
            </div>
            ${item.notes ? `<div style="font-size:0.75rem; color:#b45309; margin-top:2px;">📝 ${item.notes}</div>` : ''}
          </div>
          <div class="cart-item-price">$${lineTotal.toFixed(2)}</div>
        </div>

        <div class="cart-item-controls">
          <div class="qty-counter">
            <button class="btn-qty" onclick="updateCartQty(${item.cart_item_id}, -1)">-</button>
            <span class="qty-val">${item.quantity}</span>
            <button class="btn-qty" onclick="updateCartQty(${item.cart_item_id}, 1)">+</button>
          </div>

          <button class="btn-remove-item" onclick="removeCartItem(${item.cart_item_id})" title="លុបមុខនេះ">
            <i data-lucide="trash" style="width:16px;height:16px;"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');

  updateCartTotals();
  lucide.createIcons();
}

function updateCartQty(cartItemId, delta) {
  const item = cart.find(it => it.cart_item_id === cartItemId);
  if (!item) return;

  item.quantity += delta;
  if (item.quantity <= 0) {
    cart = cart.filter(it => it.cart_item_id !== cartItemId);
  }
  renderCart();
}

function removeCartItem(cartItemId) {
  cart = cart.filter(it => it.cart_item_id !== cartItemId);
  renderCart();
}

function clearCart() {
  if (cart.length === 0) return;
  if (confirm('តើអ្នកប្រាកដជាចង់លុបចោលបញ្ជីកុម្ម៉ង់ទាំងអស់មែនទេ?')) {
    cart = [];
    document.getElementById('discountValInput').value = '';
    renderCart();
  }
}

function toggleDiscountInput() {
  const row = document.getElementById('discountInputRow');
  row.style.display = row.style.display === 'none' ? 'block' : 'none';
}

function getCartCalculations() {
  let subtotal = 0;
  cart.forEach(item => {
    const topPrice = item.toppings.reduce((s, t) => s + t.price, 0);
    subtotal += (item.unit_price + topPrice) * item.quantity;
  });

  const discountInput = document.getElementById('discountValInput');
  const discount = discountInput ? parseFloat(discountInput.value) || 0 : 0;
  const totalUsd = Math.max(0, subtotal - discount);
  const totalKhr = Math.round((totalUsd * exchangeRate) / 100) * 100;

  return { subtotal, discount, totalUsd, totalKhr };
}

function updateCartTotals() {
  const { subtotal, discount, totalUsd, totalKhr } = getCartCalculations();

  document.getElementById('cartSubtotalUsd').innerText = `$${subtotal.toFixed(2)}`;
  document.getElementById('cartDiscountUsd').innerText = `-$${discount.toFixed(2)}`;
  document.getElementById('cartTotalUsd').innerText = `$${totalUsd.toFixed(2)}`;
  document.getElementById('cartTotalKhr').innerText = `≈ ${totalKhr.toLocaleString()} ៛`;
}

// ==================== CHECKOUT & PAYMENT MODAL ====================
function openCheckoutModal() {
  if (cart.length === 0) return;

  const { totalUsd, totalKhr } = getCartCalculations();

  document.getElementById('checkoutDueUsd').innerText = `$${totalUsd.toFixed(2)}`;
  document.getElementById('checkoutDueKhr').innerText = `≈ ${totalKhr.toLocaleString()} ៛`;

  // Reset inputs
  document.getElementById('cashReceivedUsd').value = totalUsd.toFixed(2);
  document.getElementById('cashReceivedKhr').value = '';
  calculateChange();

  // Setup KHQR preview
  switchPaymentMethod('cash');
  document.getElementById('khqrDisplayAmount').innerText = `$${totalUsd.toFixed(2)} (≈ ${totalKhr.toLocaleString()} ៛)`;
  const qrUrl = `/api/qr/generate?text=${encodeURIComponent(`KHQR:SROS_SRAY:AMOUNT=${totalUsd}:KHR=${totalKhr}`)}`;
  document.getElementById('khqrLiveImg').src = qrUrl;

  document.getElementById('checkoutModal').classList.add('show');
}

function closeCheckoutModal() {
  document.getElementById('checkoutModal').classList.remove('show');
}

function switchPaymentMethod(method) {
  activePaymentMethod = method;
  const cashBtn = document.getElementById('tabCashBtn');
  const khqrBtn = document.getElementById('tabKhqrBtn');
  const cashContent = document.getElementById('cashPaymentContent');
  const khqrContent = document.getElementById('khqrPaymentContent');

  if (method === 'cash') {
    cashBtn.classList.add('active');
    khqrBtn.classList.remove('active');
    cashContent.style.display = 'block';
    khqrContent.style.display = 'none';
  } else {
    khqrBtn.classList.add('active');
    cashBtn.classList.remove('active');
    cashContent.style.display = 'none';
    khqrContent.style.display = 'block';
  }
}

function addQuickCash(amount) {
  const { totalUsd } = getCartCalculations();
  const usdInput = document.getElementById('cashReceivedUsd');
  
  if (amount === 'exact') {
    usdInput.value = totalUsd.toFixed(2);
  } else if (amount === 'clear') {
    usdInput.value = '';
  } else {
    usdInput.value = (parseFloat(amount) || 0).toFixed(2);
  }
  document.getElementById('cashReceivedKhr').value = '';
  calculateChange();
}

function calculateChange() {
  const { totalUsd } = getCartCalculations();
  const recUsd = parseFloat(document.getElementById('cashReceivedUsd').value) || 0;
  const recKhr = parseFloat(document.getElementById('cashReceivedKhr').value) || 0;

  const totalReceivedUsd = recUsd + (recKhr / exchangeRate);
  const changeUsd = Math.max(0, totalReceivedUsd - totalUsd);
  const changeKhr = Math.round((changeUsd * exchangeRate) / 100) * 100;

  document.getElementById('changeAmountUsd').innerText = `$${changeUsd.toFixed(2)}`;
  document.getElementById('changeAmountKhr').innerText = `${changeKhr.toLocaleString()} ៛`;
}

function simulateKhqrSuccess() {
  alert('🎉 ការស្កេនទូទាត់ប្រាក់តាម KHQR ទទួលបានជោគជ័យ!');
  submitFinalOrder();
}

// ==================== SUBMIT ORDER ====================
async function submitFinalOrder() {
  const btnSubmit = document.getElementById('btnSubmitOrder');
  btnSubmit.disabled = true;
  btnSubmit.innerHTML = `<i data-lucide="loader-2" class="spin"></i> កំពុងដំណើរការ...`;
  lucide.createIcons();

  const { discount, totalUsd, totalKhr } = getCartCalculations();
  const recUsd = parseFloat(document.getElementById('cashReceivedUsd').value) || totalUsd;
  const recKhr = parseFloat(document.getElementById('cashReceivedKhr').value) || 0;

  const payload = {
    items: cart,
    payment_method: activePaymentMethod,
    discount_usd: discount,
    amount_received_usd: recUsd,
    amount_received_khr: recKhr,
    customer_note: ''
  };

  try {
    const res = await fetch('/api/order/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      playBeep('success');
      closeCheckoutModal();
      
      // Clear Cart
      cart = [];
      document.getElementById('discountValInput').value = '';
      renderCart();

      // Show Receipt Modal
      renderReceipt(result.receipt);
      document.getElementById('receiptModal').classList.add('show');
    } else {
      alert(`កំហុស៖ ${result.error || 'មិនអាចបង្កើតការកុម្ម៉ង់បានទេ'}`);
    }
  } catch (err) {
    console.error('Order submission error:', err);
    alert('មានបញ្ហាក្នុងការតភ្ជាប់ទៅកាន់ Server!');
  } finally {
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = `<i data-lucide="printer"></i> បញ្ចប់ការលក់ & បោះពុម្ពវិក្កយបត្រ`;
    lucide.createIcons();
  }
}

// ==================== RECEIPT RENDERING & PRINTING ====================
function renderReceipt(data) {
  if (!data || !data.order) return;
  const o = data.order;
  const s = data.settings || {};
  const items = data.items || [];

  const html = `
    <div class="receipt-center">
      <div class="receipt-shop-name">${s.shop_name_km || 'ហាងតែគុជ ស្រស់ស្រាយ'}</div>
      <div class="receipt-shop-sub">${s.shop_name_en || 'Sros Sray Boba & Beverage'}</div>
      <div style="font-size:11px; color:#475569;">${s.shop_address || 'រាជធានីភ្នំពេញ'}</div>
      <div style="font-size:11px; color:#475569;">ទូរស័ព្ទ៖ ${s.shop_phone || '012 345 678'}</div>
    </div>

    <div class="receipt-divider"></div>

    <div class="receipt-info-row">
      <span>លេខវិក្កយបត្រ:</span>
      <strong>${o.invoice_number}</strong>
    </div>
    <div class="receipt-info-row">
      <span>កាលបរិច្ឆេទ:</span>
      <span>${o.created_at}</span>
    </div>
    <div class="receipt-info-row">
      <span>អ្នកគិតលុយ:</span>
      <span>${o.cashier_name || 'Cashier'}</span>
    </div>
    <div class="receipt-info-row">
      <span>វិធីទូទាត់:</span>
      <span style="text-transform:uppercase; font-weight:700;">${o.payment_method}</span>
    </div>

    <div class="receipt-divider"></div>

    <table class="receipt-table">
      <thead>
        <tr>
          <th>មុខទំនិញ (Item)</th>
          <th style="text-align:center;">ចំនួន</th>
          <th style="text-align:right;">សរុប</th>
        </tr>
      </thead>
      <tbody>
        ${items.map(it => {
          const topList = it.toppings && it.toppings.length > 0 
            ? it.toppings.map(t => `+${t.topping_name}`).join(', ')
            : '';
          return `
            <tr>
              <td>
                <div style="font-weight:700;">${it.product_name} (${it.size})</div>
                <div class="receipt-item-customs">ស្ករ ${it.sugar_level}, ${it.ice_level}</div>
                ${topList ? `<div class="receipt-item-customs">${topList}</div>` : ''}
              </td>
              <td style="text-align:center; font-weight:700;">${it.quantity}</td>
              <td style="text-align:right; font-weight:700;">$${it.item_total.toFixed(2)}</td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>

    <div class="receipt-divider"></div>

    <table class="receipt-totals-table">
      <tr>
        <td>តម្លៃដើម (Subtotal):</td>
        <td style="text-align:right;">$${o.subtotal_usd.toFixed(2)}</td>
      </tr>
      ${o.discount_usd > 0 ? `
      <tr>
        <td>បញ្ចុះតម្លៃ (Discount):</td>
        <td style="text-align:right; color:#b45309;">-$${o.discount_usd.toFixed(2)}</td>
      </tr>` : ''}
      <tr class="receipt-grand-total">
        <td>សរុបត្រូវបង់ (USD):</td>
        <td style="text-align:right;">$${o.total_usd.toFixed(2)}</td>
      </tr>
      <tr style="font-weight:700; color:#059669;">
        <td>សរុបជារៀល (KHR):</td>
        <td style="text-align:right;">${o.total_khr.toLocaleString()} ៛</td>
      </tr>
      ${o.payment_method === 'cash' ? `
      <tr>
        <td>ប្រាក់ទទួល (Received):</td>
        <td style="text-align:right;">$${o.amount_received_usd.toFixed(2)}</td>
      </tr>
      <tr>
        <td>ប្រាក់អាប់ (Change):</td>
        <td style="text-align:right;">$${o.change_usd.toFixed(2)} (${o.change_khr.toLocaleString()} ៛)</td>
      </tr>` : ''}
    </table>

    <div class="receipt-divider"></div>
    <div class="receipt-footer-text">
      ${s.receipt_footer_km || 'សូមអរគុណ! សូមអញ្ជើញមកម្តងទៀត!'}
    </div>
  `;

  document.getElementById('receiptPreviewContent').innerHTML = html;
  document.getElementById('receiptPrintArea').innerHTML = html;
}

function closeReceiptModal() {
  document.getElementById('receiptModal').classList.remove('show');
}

function triggerPrintReceipt() {
  window.print();
}
