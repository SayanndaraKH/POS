// ==========================================================================
// Boba POS - Inventory & Recipe Management JS
// ==========================================================================

let availableMaterials = [];
let currentRecipeProductId = null;

document.addEventListener('DOMContentLoaded', () => {
  fetchMaterialsList();
});

async function fetchMaterialsList() {
  try {
    const res = await fetch('/api/inventory/materials');
    const data = await res.json();
    if (data.success) {
      availableMaterials = data.materials;
    }
  } catch (e) {
    console.error('Failed to fetch materials:', e);
  }
}

function switchInvTab(tabName, btn) {
  document.querySelectorAll('.inv-tab-content').forEach(c => c.style.display = 'none');
  document.querySelectorAll('.inv-tab-btn').forEach(b => {
    b.classList.remove('btn-primary', 'active');
    b.classList.add('btn-secondary');
  });

  const target = document.getElementById('tab' + tabName.charAt(0).toUpperCase() + tabName.slice(1));
  if (target) target.style.display = 'block';

  if (btn) {
    btn.classList.remove('btn-secondary');
    btn.classList.add('btn-primary', 'active');
  }
}

function closeModal(id) {
  document.getElementById(id).classList.remove('show');
}

function filterMaterialsTable() {
  const query = document.getElementById('matSearch').value.toLowerCase();
  document.querySelectorAll('.mat-row').forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
}

function filterProductsTable() {
  const query = document.getElementById('prodSearch').value.toLowerCase();
  document.querySelectorAll('.prod-row').forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
}

// ==================== STOCK IN ====================
function openStockInModal(id, name, unit) {
  document.getElementById('stockInMatId').value = id;
  document.getElementById('stockInMatName').innerText = `${name} (${unit})`;
  document.getElementById('stockInUnit').innerText = unit;
  document.getElementById('stockInQty').value = '';
  document.getElementById('stockInNotes').value = 'នាំចូលស្តុកបន្ថែម';
  document.getElementById('stockInModal').classList.add('show');
}

async function submitStockIn() {
  const id = document.getElementById('stockInMatId').value;
  const qty = parseFloat(document.getElementById('stockInQty').value);
  const notes = document.getElementById('stockInNotes').value.trim();

  if (!qty || qty <= 0) {
    alert('សូមបញ្ចូលបរិមាណនាំចូលដែលធំជាង ០!');
    return;
  }

  try {
    const res = await fetch(`/api/inventory/materials/${id}/stock-in`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity: qty, notes: notes })
    });
    const result = await res.json();
    if (result.success) {
      alert(result.message);
      location.reload();
    } else {
      alert(`កំហុស៖ ${result.error}`);
    }
  } catch (e) {
    alert('បរាជ័យក្នុងការតភ្ជាប់!');
  }
}

// ==================== MATERIALS CRUD ====================
function openAddMaterialModal() {
  document.getElementById('editMatId').value = '';
  document.getElementById('materialModalTitle').innerText = 'បន្ថែមវត្ថុធាតុដើមថ្មី';
  document.getElementById('matNameKm').value = '';
  document.getElementById('matNameEn').value = '';
  document.getElementById('matUnit').value = 'pcs';
  document.getElementById('matInitialStock').value = '0';
  document.getElementById('matMinAlert').value = '10';
  document.getElementById('matCostPerUnit').value = '0.00';
  document.getElementById('initialStockGroup').style.display = 'block';
  document.getElementById('materialModal').classList.add('show');
}

function openEditMaterialModal(id, nameKm, nameEn, unit, minAlert, cost) {
  document.getElementById('editMatId').value = id;
  document.getElementById('materialModalTitle').innerText = 'កែប្រែព័ត៌មានវត្ថុធាតុដើម';
  document.getElementById('matNameKm').value = nameKm;
  document.getElementById('matNameEn').value = nameEn;
  document.getElementById('matUnit').value = unit;
  document.getElementById('matMinAlert').value = minAlert;
  document.getElementById('matCostPerUnit').value = cost;
  document.getElementById('initialStockGroup').style.display = 'none';
  document.getElementById('materialModal').classList.add('show');
}

async function submitMaterialForm() {
  const editId = document.getElementById('editMatId').value;
  const nameKm = document.getElementById('matNameKm').value.trim();
  const nameEn = document.getElementById('matNameEn').value.trim();
  const unit = document.getElementById('matUnit').value;
  const initialStock = parseFloat(document.getElementById('matInitialStock').value) || 0;
  const minAlert = parseFloat(document.getElementById('matMinAlert').value) || 10;
  const cost = parseFloat(document.getElementById('matCostPerUnit').value) || 0;

  if (!nameKm) {
    alert('សូមបញ្ចូលឈ្មោះជាភាសាខ្មែរ!');
    return;
  }

  const payload = {
    name_km: nameKm,
    name_en: nameEn,
    unit: unit,
    current_stock: initialStock,
    min_threshold: minAlert,
    cost_per_unit: cost
  };

  try {
    const url = editId ? `/api/inventory/materials/${editId}` : '/api/inventory/materials';
    const method = editId ? 'PUT' : 'POST';
    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      alert(result.message);
      location.reload();
    } else {
      alert(`កំហុស៖ ${result.error}`);
    }
  } catch (e) {
    alert('បរាជ័យក្នុងការរក្សាទុក!');
  }
}

async function deleteMaterial(id, name) {
  if (confirm(`តើអ្នកប្រាកដជាចង់លុប "${name}" ចេញពីប្រព័ន្ធមែនទេ?`)) {
    try {
      const res = await fetch(`/api/inventory/materials/${id}`, { method: 'DELETE' });
      const result = await res.json();
      if (result.success) {
        alert(result.message);
        location.reload();
      } else {
        alert(result.error);
      }
    } catch (e) {
      alert('បរាជ័យក្នុងការលុប!');
    }
  }
}

// ==================== PRODUCTS CRUD ====================
function openAddProductModal() {
  document.getElementById('editProdId').value = '';
  document.getElementById('productModalTitle').innerText = 'បន្ថែមភេសជ្ជៈថ្មី';
  document.getElementById('prodNameKm').value = '';
  document.getElementById('prodNameEn').value = '';
  document.getElementById('prodCode').value = '';
  document.getElementById('prodBasePrice').value = '2.00';
  document.getElementById('prodDesc').value = '';
  document.getElementById('prodAvailable').value = '1';
  document.getElementById('productModal').classList.add('show');
}

function openEditProductModal(id, catId, nameKm, nameEn, code, price, img, desc, avail) {
  document.getElementById('editProdId').value = id;
  document.getElementById('productModalTitle').innerText = 'កែប្រែភេសជ្ជៈ';
  document.getElementById('prodCategory').value = catId;
  document.getElementById('prodNameKm').value = nameKm;
  document.getElementById('prodNameEn').value = nameEn || '';
  document.getElementById('prodCode').value = code || '';
  document.getElementById('prodBasePrice').value = price;
  document.getElementById('prodImage').value = img || '/static/images/brown_sugar_boba.svg';
  document.getElementById('prodDesc').value = desc || '';
  document.getElementById('prodAvailable').value = avail ? '1' : '0';
  document.getElementById('productModal').classList.add('show');
}

async function submitProductForm() {
  const editId = document.getElementById('editProdId').value;
  const nameKm = document.getElementById('prodNameKm').value.trim();
  const nameEn = document.getElementById('prodNameEn').value.trim();
  const catId = parseInt(document.getElementById('prodCategory').value);
  const code = document.getElementById('prodCode').value.trim();
  const price = parseFloat(document.getElementById('prodBasePrice').value);
  const img = document.getElementById('prodImage').value;
  const desc = document.getElementById('prodDesc').value.trim();
  const avail = document.getElementById('prodAvailable').value === '1';

  if (!nameKm || isNaN(price)) {
    alert('សូមបំពេញឈ្មោះភេសជ្ជៈ និងតម្លៃលក់ឱ្យបានត្រឹមត្រូវ!');
    return;
  }

  const payload = {
    category_id: catId,
    name_km: nameKm,
    name_en: nameEn,
    code: code,
    base_price: price,
    image_url: img,
    description: desc,
    is_available: avail
  };

  try {
    const url = editId ? `/api/inventory/products/${editId}` : '/api/inventory/products';
    const method = editId ? 'PUT' : 'POST';
    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      alert(result.message);
      location.reload();
    } else {
      alert(`កំហុស៖ ${result.error}`);
    }
  } catch (e) {
    alert('បរាជ័យក្នុងការរក្សាទុក!');
  }
}

async function deleteProduct(id, name) {
  if (confirm(`តើអ្នកប្រាកដជាចង់លុបភេសជ្ជៈ "${name}" មែនទេ?`)) {
    try {
      const res = await fetch(`/api/inventory/products/${id}`, { method: 'DELETE' });
      const result = await res.json();
      if (result.success) {
        alert(result.message);
        location.reload();
      } else {
        alert(result.error);
      }
    } catch (e) {
      alert('បរាជ័យក្នុងការលុប!');
    }
  }
}

// ==================== RECIPE / BOM EDITOR ====================
async function openRecipeModal(productId, productName) {
  currentRecipeProductId = productId;
  document.getElementById('recipeProdName').innerText = productName;
  const container = document.getElementById('recipeItemsList');
  container.innerHTML = '<div style="text-align:center; padding:1rem;">កំពុងផ្ទុករូបមន្ត...</div>';
  document.getElementById('recipeModal').classList.add('show');

  try {
    const res = await fetch(`/api/inventory/recipes/${productId}`);
    const data = await res.json();
    if (data.success) {
      renderRecipeRows(data.recipes);
    }
  } catch (e) {
    container.innerHTML = '<div style="color:red;">បរាជ័យក្នុងការផ្ទុករូបមន្ត!</div>';
  }
}

function renderRecipeRows(recipes) {
  const container = document.getElementById('recipeItemsList');
  if (!recipes || recipes.length === 0) {
    container.innerHTML = `<div id="emptyRecipeMsg" style="text-align:center; color:#94a3b8; padding:1rem;">មិនទាន់មានវត្ថុធាតុដើមកំណត់ក្នុងរូបមន្តនេះទេ</div>`;
    return;
  }

  container.innerHTML = recipes.map((r, i) => createRecipeRowHtml(r, i)).join('');
  lucide.createIcons();
}

function createRecipeRowHtml(r = {}, index = Date.now()) {
  const matOptions = availableMaterials.map(m => `
    <option value="${m.id}" ${r.raw_material_id == m.id ? 'selected' : ''}>
      ${m.name_km} (${m.unit})
    </option>
  `).join('');

  return `
    <div class="recipe-row-item" style="display:flex; gap:8px; align-items:center; background:#f8fafc; padding:8px; border-radius:8px; border:1px solid #e2e8f0;">
      <select class="form-control rec-mat-select" style="flex:2; font-size:0.85rem;">
        ${matOptions}
      </select>
      <input type="number" class="form-control rec-qty-input" style="flex:1; font-size:0.85rem;" placeholder="បរិមាណ" value="${r.quantity_used || 1}" step="0.5" min="0.1">
      <select class="form-control rec-size-select" style="flex:1; font-size:0.85rem;">
        <option value="ALL" ${r.for_size == 'ALL' ? 'selected' : ''}>គ្រប់ទំហំ</option>
        <option value="M" ${r.for_size == 'M' ? 'selected' : ''}>កែវ M</option>
        <option value="L" ${r.for_size == 'L' ? 'selected' : ''}>កែវ L</option>
      </select>
      <button type="button" class="btn btn-danger" style="padding:6px 8px;" onclick="this.parentElement.remove()">
        <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
      </button>
    </div>
  `;
}

function addRecipeRow() {
  const container = document.getElementById('recipeItemsList');
  const emptyMsg = document.getElementById('emptyRecipeMsg');
  if (emptyMsg) emptyMsg.remove();

  const temp = document.createElement('div');
  temp.innerHTML = createRecipeRowHtml();
  container.appendChild(temp.firstElementChild);
  lucide.createIcons();
}

async function submitRecipeForm() {
  if (!currentRecipeProductId) return;

  const rows = document.querySelectorAll('.recipe-row-item');
  const recipes = [];

  rows.forEach(row => {
    const matId = parseInt(row.querySelector('.rec-mat-select').value);
    const qty = parseFloat(row.querySelector('.rec-qty-input').value) || 1;
    const size = row.querySelector('.rec-size-select').value;
    recipes.push({
      raw_material_id: matId,
      quantity_used: qty,
      for_size: size
    });
  });

  try {
    const res = await fetch(`/api/inventory/recipes/${currentRecipeProductId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipes: recipes })
    });
    const result = await res.json();
    if (result.success) {
      alert(result.message);
      closeModal('recipeModal');
    } else {
      alert(result.error);
    }
  } catch (e) {
    alert('បរាជ័យក្នុងការរក្សាទុករូបមន្ត!');
  }
}

// ==================== TOPPINGS CRUD ====================
function openAddToppingModal() {
  document.getElementById('editTopId').value = '';
  document.getElementById('toppingModalTitle').innerText = 'បន្ថែម Topping ថ្មី';
  document.getElementById('topNameKm').value = '';
  document.getElementById('topNameEn').value = '';
  document.getElementById('topPrice').value = '0.35';
  document.getElementById('topRawMaterial').value = '';
  document.getElementById('topDeductAmount').value = '0';
  document.getElementById('toppingModal').classList.add('show');
}

function openEditToppingModal(id, nameKm, nameEn, price, matId, deductAmt, avail) {
  document.getElementById('editTopId').value = id;
  document.getElementById('toppingModalTitle').innerText = 'កែប្រែ Topping';
  document.getElementById('topNameKm').value = nameKm;
  document.getElementById('topNameEn').value = nameEn || '';
  document.getElementById('topPrice').value = price;
  document.getElementById('topRawMaterial').value = matId || '';
  document.getElementById('topDeductAmount').value = deductAmt || 0;
  document.getElementById('toppingModal').classList.add('show');
}

async function submitToppingForm() {
  const editId = document.getElementById('editTopId').value;
  const nameKm = document.getElementById('topNameKm').value.trim();
  const nameEn = document.getElementById('topNameEn').value.trim();
  const price = parseFloat(document.getElementById('topPrice').value);
  const matId = document.getElementById('topRawMaterial').value;
  const deduct = parseFloat(document.getElementById('topDeductAmount').value) || 0;

  if (!nameKm || isNaN(price)) {
    alert('សូមបំពេញព័ត៌មាន Topping ឱ្យបានត្រឹមត្រូវ!');
    return;
  }

  const payload = {
    name_km: nameKm,
    name_en: nameEn,
    price: price,
    raw_material_id: matId ? parseInt(matId) : null,
    deduction_amount: deduct,
    is_available: true
  };

  try {
    const url = editId ? `/api/inventory/toppings/${editId}` : '/api/inventory/toppings';
    const method = editId ? 'PUT' : 'POST';
    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.success) {
      alert(result.message);
      location.reload();
    } else {
      alert(result.error);
    }
  } catch (e) {
    alert('បរាជ័យក្នុងការរក្សាទុក Topping!');
  }
}

async function deleteTopping(id, name) {
  if (confirm(`តើអ្នកប្រាកដជាចង់លុប Topping "${name}" មែនទេ?`)) {
    try {
      const res = await fetch(`/api/inventory/toppings/${id}`, { method: 'DELETE' });
      const result = await res.json();
      if (result.success) {
        alert(result.message);
        location.reload();
      } else {
        alert(result.error);
      }
    } catch (e) {
      alert('បរាជ័យក្នុងការលុប!');
    }
  }
}
