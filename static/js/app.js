const cartKey = 'cafeteria_cart';
const productGrid = document.getElementById('product-grid');
const cartItems = document.getElementById('cart-items');
const cartTotal = document.getElementById('cart-total');
const cartPayload = document.getElementById('cart-payload');
const checkoutForm = document.getElementById('checkout-form');
const clearCartBtn = document.getElementById('clear-cart');
const productModal = document.getElementById('product-modal');
const modalClose = document.getElementById('modal-close');
const modalImage = document.getElementById('modal-image');
const modalCategory = document.getElementById('modal-category');
const modalName = document.getElementById('modal-name');
const modalDescription = document.getElementById('modal-description');
const modalPrice = document.getElementById('modal-price');
const modalOldPrice = document.getElementById('modal-old-price');
const ingredientSelects = document.getElementById('ingredient-selects');
const modalQuantity = document.getElementById('modal-quantity');
const addToCartBtn = document.getElementById('add-to-cart');
const paymentMethod = document.getElementById('payment-method');
const paymentModal = document.getElementById('payment-modal');
const paymentModalClose = document.getElementById('payment-modal-close');
const cardPayBtn = document.getElementById('card-pay');
const cardCancelBtn = document.getElementById('card-cancel');
const cardAmountInput = document.getElementById('card-amount');
const cardNumberInput = document.getElementById('card-number');
const cardBankInput = document.getElementById('card-bank');
const cardTypeSelect = document.getElementById('card-type');
let paymentConfirmed = false;
const filterButtons = document.querySelectorAll('.chip[data-filter]');
const socket = typeof io !== 'undefined' ? io() : null;

let currentProduct = null;

function loadCart() {
  return JSON.parse(localStorage.getItem(cartKey) || '[]');
}

function saveCart(cart) {
  localStorage.setItem(cartKey, JSON.stringify(cart));
  renderCart();
}

function money(value) {
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value || 0);
}

function cartTotalValue(cart) {
  return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
}

function renderCart() {
  if (!cartItems || !cartTotal || !cartPayload) return;
  const cart = loadCart();
  cartItems.innerHTML = '';
  if (!cart.length) {
    cartItems.innerHTML = '<p class="muted">Tu carrito está vacío.</p>';
  } else {
    cart.forEach((item, index) => {
      const article = document.createElement('div');
      article.className = 'cart-item';
      article.innerHTML = `
        <div class="cart-item-top">
          <div>
            <strong>${item.name}</strong>
            <p class="muted">${money(item.price)} cada uno</p>
          </div>
          <button type="button" data-remove="${index}" class="qty-remove">×</button>
        </div>
        <div class="qty-controls">
          <button type="button" data-dec="${index}">-</button>
          <strong>${item.quantity}</strong>
          <button type="button" data-inc="${index}">+</button>
        </div>
        <p class="muted">${Object.entries(item.ingredients || {}).map(([key, value]) => `${key}: ${value}`).join(' | ') || 'Sin extras'}</p>
      `;
      cartItems.appendChild(article);
    });
  }
  cartTotal.textContent = money(cartTotalValue(cart));
  cartPayload.value = JSON.stringify(cart);
}

function addItemToCart(product, quantity, ingredients) {
  const cart = loadCart();
  const existingIndex = cart.findIndex(item => item.id === product.id && JSON.stringify(item.ingredients || {}) === JSON.stringify(ingredients || {}));
  if (existingIndex >= 0) {
    cart[existingIndex].quantity += quantity;
  } else {
    cart.push({
      id: product.id,
      name: product.name,
      price: product.price,
      quantity,
      ingredients,
      image_url: product.image_url,
    });
  }
  saveCart(cart);
}

function openModal(product) {
  currentProduct = product;
  modalImage.src = product.image_url;
  modalCategory.textContent = product.category;
  modalName.textContent = product.name;
  modalDescription.textContent = product.description;
  modalPrice.textContent = money(product.price);
  modalOldPrice.textContent = product.discount_price ? money(product.base_price) : '';
  modalOldPrice.style.display = product.discount_price ? 'inline-block' : 'none';
  ingredientSelects.innerHTML = '';
  const options = product.ingredient_options ? JSON.parse(product.ingredient_options || '{}') : {};
  Object.entries(options).forEach(([label, values]) => {
    if (!values || !values.length) return;
    const field = document.createElement('div');
    field.innerHTML = `
      <label>${label}</label>
      <select data-ingredient-key="${label}">
        ${values.map(value => `<option value="${value}">${value}</option>`).join('')}
      </select>
    `;
    ingredientSelects.appendChild(field);
  });
  modalQuantity.value = 1;
  productModal.classList.add('open');
  productModal.setAttribute('aria-hidden', 'false');
}

function closeModal() {
  productModal.classList.remove('open');
  productModal.setAttribute('aria-hidden', 'true');
}

function updateCartInteraction(e) {
  const target = e.target;
  const cart = loadCart();
  if (target.dataset.inc !== undefined) {
    cart[target.dataset.inc].quantity += 1;
    saveCart(cart);
  }
  if (target.dataset.dec !== undefined) {
    const index = Number(target.dataset.dec);
    cart[index].quantity -= 1;
    if (cart[index].quantity <= 0) {
      cart.splice(index, 1);
    }
    saveCart(cart);
  }
  if (target.dataset.remove !== undefined) {
    cart.splice(Number(target.dataset.remove), 1);
    saveCart(cart);
  }
}

if (productGrid) {
  productGrid.addEventListener('click', (event) => {
    const card = event.target.closest('.product-card');
    if (!card || card.classList.contains('is-disabled')) return;
    const product = JSON.parse(card.dataset.product);
    openModal(product);
  });

  filterButtons.forEach(button => {
    button.addEventListener('click', () => {
      filterButtons.forEach(btn => btn.classList.remove('active'));
      button.classList.add('active');
      const filter = button.dataset.filter;
      document.querySelectorAll('.product-card').forEach(card => {
        const visible = filter === 'all' || card.dataset.category === filter;
        card.style.display = visible ? 'block' : 'none';
      });
    });
  });
}

if (modalClose) {
  modalClose.addEventListener('click', closeModal);
}

if (productModal) {
  productModal.addEventListener('click', (event) => {
    if (event.target === productModal) closeModal();
  });
}

if (addToCartBtn) {
  addToCartBtn.addEventListener('click', () => {
    if (!currentProduct) return;
    const ingredients = {};
    ingredientSelects.querySelectorAll('select').forEach(select => {
      ingredients[select.dataset.ingredientKey] = select.value;
    });
    addItemToCart(currentProduct, Math.max(1, Number(modalQuantity.value || 1)), ingredients);
    closeModal();
  });
}

if (cartItems) {
  cartItems.addEventListener('click', updateCartInteraction);
}

if (clearCartBtn) {
  clearCartBtn.addEventListener('click', () => saveCart([]));
}

if (checkoutForm) {
  checkoutForm.addEventListener('submit', (event) => {
    const cart = loadCart();
    if (!cart.length) {
      event.preventDefault();
      alert('Tu carrito está vacío.');
      return;
    }
    // Simulated card flow: show payment modal first
    if (paymentMethod && paymentMethod.value === 'tarjeta' && !paymentConfirmed) {
      event.preventDefault();
      // fill amount
      cardAmountInput.value = money(cartTotalValue(cart));
      // show modal
      if (paymentModal) {
        paymentModal.classList.add('open');
        paymentModal.setAttribute('aria-hidden', 'false');
      }
      return;
    }

    if (paymentMethod && paymentMethod.value === 'efectivo') {
      alert('puedes acercarte a caja y cancelar para continuar con tu orden');
    }

    // Only clear cart after confirmed submission (either cash or card confirmed)
    if (paymentMethod && (paymentMethod.value === 'efectivo' || paymentConfirmed)) {
      localStorage.removeItem(cartKey);
      paymentConfirmed = false;
    }
  });
}

function closePaymentModal() {
  if (!paymentModal) return;
  paymentModal.classList.remove('open');
  paymentModal.setAttribute('aria-hidden', 'true');
}

if (paymentModalClose) {
  paymentModalClose.addEventListener('click', () => {
    closePaymentModal();
  });
}

if (cardCancelBtn) {
  cardCancelBtn.addEventListener('click', () => {
    // just close modal and do nothing
    closePaymentModal();
  });
}

if (cardPayBtn) {
  cardPayBtn.addEventListener('click', () => {
    const number = cardNumberInput ? (cardNumberInput.value || '').replace(/\s+/g, '') : '';
    const bank = cardBankInput ? (cardBankInput.value || '').trim() : '';
    if (!bank) { alert('Ingresa el banco emisor.'); return; }
    if (!/^[0-9]{12,19}$/.test(number)) { alert('Número de tarjeta inválido. Debe tener entre 12 y 19 dígitos.'); return; }

    // simulate processing
    cardPayBtn.disabled = true;
    cardPayBtn.textContent = 'Procesando...';
    setTimeout(() => {
      // mark as confirmed and submit original form
      paymentConfirmed = true;
      closePaymentModal();
      cardPayBtn.disabled = false;
      cardPayBtn.textContent = 'Pagar';
      if (checkoutForm) checkoutForm.submit();
    }, 900);
  });
}

if (socket) {
  socket.on('products_updated', () => {
    if (productGrid) location.reload();
  });
  socket.on('orders_updated', () => {
    if (document.querySelector('.orders-list') || document.querySelector('.kitchen-list')) {
      location.reload();
    }
  });
}

renderCart();