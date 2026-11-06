/**
 * VOID STORE — GLOBAL MAIN SCRIPT
 * Vanilla JS client infrastructure: Cart Drawer, Toasts, Route Transitions
 */

(() => {
  'use strict';

  // CSRF token retrieval helper
  function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf"]');
    return meta ? meta.content : '';
  }

  // Toast Notification System
  const toastEl = document.getElementById('toast');
  let toastTimer = null;

  window.showToast = function(message) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.classList.add('is-visible');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastEl.classList.remove('is-visible');
    }, 2800);
  };

  // Header Bag Badge Updater
  window.updateCartBadge = function(count) {
    document.querySelectorAll('[data-cart-count]').forEach(el => {
      el.textContent = count;
      el.classList.remove('bounce');
      void el.offsetWidth; // trigger reflow
      el.classList.add('bounce');
    });
  };

  // Cart Drawer Controller
  const drawer = document.getElementById('cart-drawer');
  const backdrop = document.getElementById('cart-drawer-backdrop');
  const openBagBtn = document.getElementById('open-bag');
  const closeBtn = document.getElementById('drawer-close-btn');

  function openDrawer() {
    if (!drawer || !backdrop) return;
    drawer.hidden = false;
    // Allow DOM render then animate
    requestAnimationFrame(() => {
      drawer.classList.add('is-open');
      backdrop.classList.add('is-open');
      if (openBagBtn) openBagBtn.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    });
  }

  function closeDrawer() {
    if (!drawer || !backdrop) return;
    drawer.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    if (openBagBtn) openBagBtn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    setTimeout(() => {
      if (!drawer.classList.contains('is-open')) {
        drawer.hidden = true;
      }
    }, 500);
  }

  window.openCartDrawer = openDrawer;
  window.closeCartDrawer = closeDrawer;

  if (openBagBtn) {
    openBagBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (drawer && drawer.classList.contains('is-open')) {
        closeDrawer();
      } else {
        openDrawer();
      }
    });
  }

  if (closeBtn) closeBtn.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && drawer && drawer.classList.contains('is-open')) {
      closeDrawer();
    }
  });

  // Re-render Cart Drawer HTML from JSON Payload
  window.renderCartDrawer = function(data) {
    window.updateCartBadge(data.count);

    const itemsContainer = document.getElementById('drawer-items-container');
    const footerBlock = document.getElementById('drawer-footer-block');
    const subtotalEl = document.getElementById('drawer-subtotal-val');
    const discountRow = document.getElementById('drawer-discount-row');
    const discountEl = document.getElementById('drawer-discount-val');
    const totalEl = document.getElementById('drawer-total-val');

    if (!itemsContainer) return;

    if (!data.items || data.items.length === 0) {
      itemsContainer.innerHTML = `
        <div class="drawer-empty-state">
          <p class="drawer-empty-title">Your bag is empty.</p>
          <p class="drawer-empty-sub">Explore the runway or catalog to add streetwear essentials.</p>
          <a href="/shop/" class="btn-dark sm" onclick="window.closeCartDrawer()">Explore Catalog</a>
        </div>
      `;
      if (footerBlock) footerBlock.style.display = 'none';
      return;
    }

    if (footerBlock) footerBlock.style.display = 'flex';
    if (subtotalEl) subtotalEl.textContent = `$${data.subtotal}`;
    if (totalEl) totalEl.textContent = `$${data.total}`;

    const disc = parseFloat(data.discount) || 0;
    if (discountRow && discountEl) {
      if (disc > 0) {
        discountRow.style.display = 'flex';
        discountEl.textContent = `−$${data.discount}`;
      } else {
        discountRow.style.display = 'none';
      }
    }

    let html = '<ul class="drawer-items-list">';
    data.items.forEach(it => {
      html += `
        <li class="drawer-item" data-item-id="${it.id}">
          <div class="drawer-item-img">
            <img src="/static/${it.image}" alt="${it.name}">
          </div>
          <div class="drawer-item-info">
            <span class="drawer-item-vendor">VOID ARCHIVE</span>
            <a href="/shop/" class="drawer-item-name">${it.name}</a>
            <span class="drawer-item-size">Size: ${it.size}</span>
            ${it.is_bundle ? '<span class="bundle-badge">10% Look Bundle Applied</span>' : ''}
            <div class="drawer-qty-row">
              <div class="drawer-qty-controls">
                <button class="drawer-qty-btn" onclick="updateDrawerQty(${it.id}, ${it.qty - 1})" aria-label="Decrease quantity">−</button>
                <span class="drawer-qty-val">${it.qty}</span>
                <button class="drawer-qty-btn" onclick="updateDrawerQty(${it.id}, ${it.qty + 1})" aria-label="Increase quantity">+</button>
              </div>
              <span class="drawer-item-price">$${it.line_total}</span>
            </div>
          </div>
          <button class="drawer-remove-btn" onclick="removeDrawerItem(${it.id})" aria-label="Remove ${it.name}">×</button>
        </li>
      `;
    });
    html += '</ul>';
    itemsContainer.innerHTML = html;
  };

  // Quantity modification in Drawer
  window.updateDrawerQty = async function(itemId, newQty) {
    try {
      const resp = await fetch('/cart/update/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'fetch',
          'X-CSRFToken': getCsrfToken()
        },
        body: new URLSearchParams({ item_id: itemId, quantity: newQty })
      });
      const data = await resp.json();
      if (resp.ok && data.ok) {
        window.fetchLatestDrawerData();
        window.showToast(data.message);
      } else {
        window.showToast(data.message || "Failed to update quantity.");
      }
    } catch (e) {
      window.showToast("Network error. Please try again.");
    }
  };

  // Remove Item from Drawer
  window.removeDrawerItem = async function(itemId) {
    try {
      const resp = await fetch('/cart/remove/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-Requested-With': 'fetch',
          'X-CSRFToken': getCsrfToken()
        },
        body: new URLSearchParams({ item_id: itemId })
      });
      const data = await resp.json();
      if (resp.ok && data.ok) {
        window.fetchLatestDrawerData();
        window.showToast(data.message);
      }
    } catch (e) {
      window.showToast("Network error. Please try again.");
    }
  };

  // Fetch Latest Drawer Data
  window.fetchLatestDrawerData = async function() {
    try {
      const resp = await fetch('/cart/drawer-data/', {
        headers: { 'X-Requested-With': 'fetch' }
      });
      if (resp.ok) {
        const data = await resp.json();
        window.renderCartDrawer(data);
      }
    } catch (e) {
      console.warn("Could not fetch cart drawer data", e);
    }
  };

  // Page Transition Curtain
  document.addEventListener('DOMContentLoaded', () => {
    const curtain = document.getElementById('page-curtain');
    if (curtain) {
      curtain.style.opacity = '0';
    }

    // Scroll-triggered subtle reveals
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.product-card, .comp-card, .look-reference-card').forEach(el => {
      observer.observe(el);
    });
  });

})();
