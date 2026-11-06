/**
 * VOID STORE — RUNWAY 3D HERO CAROUSEL CUSTOM ELEMENT
 * Exact pixel-level recreation matching runway-spec.md
 */

(() => {
  'use strict';

  class RunwaySection extends HTMLElement {
    connectedCallback() {
      if (this._initialized) return;
      this._initialized = true;

      // Extract looks JSON data embedded from Django context
      const looksDataEl = document.getElementById('rw-looks-data');
      if (!looksDataEl) return;

      this.looks = JSON.parse(looksDataEl.textContent);
      this.n = this.looks.length;
      this.N = this.n * 2; // 12 bodies (6 originals + 6 clones)
      this.step = (Math.PI * 2) / this.N;
      this.K = 95;
      this.C = 2 * Math.sqrt(this.K); // 19.49 critically damped
      this.speed = parseInt(this.dataset.speed, 10) || 5000;

      this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      this.csrf = document.querySelector('meta[name="csrf"]')?.content || '';

      // Stage & Actor element handles
      this.stage = this.querySelector('[data-rw-stage]');
      this.actors = this.querySelector('[data-rw-actors]');
      this.heroes = this.querySelector('[data-rw-heroes]');
      this.panels = [...this.querySelectorAll('.rw__look-panel')];
      this.ticks = [...this.querySelectorAll('.rw__tick')];
      this.liveEl = this.querySelector('[data-rw-live]');
      this.piecesLabel = this.querySelector('[data-rw-pieces]');
      this.autoBtn = this.querySelector('[data-rw-auto]');
      this.prevBtn = this.querySelector('[data-rw-prev]');
      this.nextBtn = this.querySelector('[data-rw-next]');
      this.cursor = this.querySelector('[data-rw-cursor]');
      this.cursorIn = this.querySelector('.rw__cursor-in');
      this.lightbox = document.getElementById('rw-lightbox');

      // Carousel Simulation State
      this.cur = this.reducedMotion ? 0 : -1.15;
      this.target = 0;
      this.vel = 0;
      this.index = 0;
      this.raf = 0;
      this.lastTime = 0;
      this.still = false;
      this.dragging = false;
      this.playing = !this.reducedMotion;
      this.engaged = false;
      this.panelHover = false;
      this.timer = null;

      // Pointer drag state
      this.startX = 0;
      this.startY = 0;
      this.startTarget = 0;
      this.pointerId = null;
      this.samples = [];
      this.suppressClick = 0;

      // Cursor physics
      this.cursorX = 0;
      this.cursorY = 0;
      this.targetCursorX = 0;
      this.targetCursorY = 0;
      this.cursorRaf = 0;

      this.initBodies();
      this.initFeetDetection();
      this.initControls();
      this.initDrag();
      this.initCursor();
      this.initLightbox();
      this.initCartActions();

      // Measure & Start
      this.measure();
      window.addEventListener('resize', () => this.measure());
      new ResizeObserver(() => this.measure()).observe(this.stage);

      this.setIndex(0, true);
      this.render();
      this.kick();

      if (this.playing) {
        this.restartAutoplay();
      }
    }

    /* ----------------------------------------------------
       1. BODIES INITIALIZATION (6 Originals + 6 Clones)
       ---------------------------------------------------- */
    initBodies() {
      this.bodies = [];
      for (let a = 0; a < this.N; a++) {
        const look = this.looks[a % this.n];
        const body = document.createElement('div');
        body.className = 'rw__model';
        body.dataset.bodyIdx = a;

        const isClone = a >= this.n;
        body.innerHTML = `
          <div class="rw__shadow"></div>
          <div class="rw__art" data-rw-art>
            <img src="/static/${look.img}" 
                 srcset="/static/${look.img} 640w, /static/${look.hd} 1080w" 
                 sizes="(min-width: 1800px) 540px, (min-width: 750px) 420px, 320px" 
                 alt="${look.name}" 
                 draggable="false" 
                 loading="${isClone ? 'lazy' : 'eager'}" 
                 decoding="async">
          </div>
          <button class="rw__hit" tabindex="-1" data-rw-hit="${a}" aria-label="Look ${a % this.n + 1}: ${look.name}"></button>
        `;

        this.actors.appendChild(body);
        this.bodies.push(body);
      }
    }

    /* ----------------------------------------------------
       2. FEET DETECTION VIA OFFSCREEN CANVAS PROBE
       ---------------------------------------------------- */
    initFeetDetection() {
      this.looks.forEach((look, i) => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.src = `/static/${look.img}`;
        img.onload = () => {
          try {
            const probeW = 48;
            const probeH = Math.round((img.naturalHeight / img.naturalWidth) * probeW) || 85;
            const canvas = document.createElement('canvas');
            canvas.width = probeW;
            canvas.height = probeH;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, probeW, probeH);

            const imgData = ctx.getImageData(0, 0, probeW, probeH).data;
            let lastRow = probeH - 1;
            outer: for (let y = probeH - 1; y >= 0; y--) {
              for (let x = 0; x < probeW; x++) {
                const alpha = imgData[(y * probeW + x) * 4 + 3];
                if (alpha > 40) {
                  lastRow = y;
                  break outer;
                }
              }
            }

            const footFraction = Math.max(0, Math.min(0.4, (probeH - 1 - lastRow) / probeH));
            // Apply --rw-foot to bodies and hero
            this.bodies.forEach((b, a) => {
              if (a % this.n === i) {
                b.style.setProperty('--rw-foot', footFraction.toFixed(4));
              }
            });
            const matchingHero = this.heroes.querySelector(`[data-hero="${i}"]`);
            if (matchingHero) {
              matchingHero.style.setProperty('--rw-foot', footFraction.toFixed(4));
            }
          } catch (e) {
            // Silently keep default 0 on canvas error
          }
        };
      });
    }

    /* ----------------------------------------------------
       3. MEASURE & DIMENSIONS
       ---------------------------------------------------- */
    measure() {
      const W = this.stage.clientWidth;
      const H = this.stage.clientHeight;
      const isMob = W < 750;

      // Model Height: modelH = max(200, round((H - 34 - 18) / 1.08))
      const modelH = Math.max(200, Math.round((H - 34 - 18) / 1.08));
      this.stage.style.setProperty('--rw-model-h', `${modelH}px`);

      if (isMob) {
        this.stage.style.setProperty('--rw-hx', `${(0.3 * W).toFixed(1)}px`);
        this.stage.style.setProperty('--rw-hy', '22px');
        this.stage.style.setProperty('--rw-fs', '1');
      } else {
        this.stage.style.setProperty('--rw-hx', `${(0.5 * W).toFixed(1)}px`);
        this.stage.style.setProperty('--rw-hy', '34px');
        this.stage.style.setProperty('--rw-fs', '1.08');
      }

      this.unit = Math.max(isMob ? 90 : 120, W * (isMob ? 0.32 * 1.6 : 0.3));
    }

    /* ----------------------------------------------------
       4. 3D RING RENDERING LOOP & MATH
       ---------------------------------------------------- */
    render() {
      const W = this.stage.clientWidth;
      const H = this.stage.clientHeight;
      if (!W || !H) return;

      const isMob = W < 750;
      const cx = 0.5 * W;
      const R = (isMob ? 0.72 : 0.62) * W;
      const P = (isMob ? 1.9 : 1.65) * W;
      const floor = H - (isMob ? 24 : 34);
      const horizon = 0.36 * H;
      const fs = isMob ? 1 : 1.08;

      this.bodies.forEach((b, a) => {
        let phi = ((a - this.cur) * this.step) % (Math.PI * 2);
        if (phi > Math.PI) phi -= Math.PI * 2;
        if (phi <= -Math.PI) phi += Math.PI * 2;

        const z = R * (1 - Math.cos(phi));
        const persp = P / (P + z);
        const sl = Math.abs(phi) / this.step;
        const scale = persp * (1 + (fs - 1) * Math.min(1, Math.max(0, 1 - sl)));
        const x = cx + R * Math.sin(phi) * persp;
        const feet = horizon + (floor - horizon) * persp;
        const bottom = H - feet;

        const blur = sl <= 1 ? 1.8 * sl : Math.min(1.8 + (sl - 1) * 2, 6.5);
        let opacity = Math.min(1, Math.max(0, (Math.cos(phi) + 0.55) / 0.3));

        // Mark front body
        const isFront = sl < 0.05;
        b.classList.toggle('is-front', isFront);

        // Offscreen culling
        const bodyW = 320 * scale;
        if (x + bodyW / 2 < -10 || x - bodyW / 2 > W + 10) {
          opacity = 0;
        }

        b.style.transform = `translate3d(${x.toFixed(1)}px, ${(-bottom).toFixed(1)}px, 0) translateX(-50%) scale(${scale.toFixed(4)})`;
        b.style.opacity = opacity.toFixed(3);
        b.style.zIndex = Math.round(scale * 1000);
        b.style.visibility = opacity < 0.01 ? 'hidden' : 'visible';
        b.style.pointerEvents = opacity < 0.5 ? 'none' : 'auto';
        b.style.filter = blur > 0.05 ? `blur(${blur.toFixed(1)}px)` : '';
      });
    }

    frame(t) {
      const dt = Math.min(0.034, (t - (this.lastTime || t - 16.7)) / 1000);
      this.lastTime = t;

      if (this.reducedMotion) {
        this.cur = this.target;
        this.vel = 0;
      } else {
        // 3 sub-steps for smooth spring integration
        for (let i = 0; i < 3; i++) {
          const h = dt / 3;
          const acc = -this.K * (this.cur - this.target) - this.C * this.vel;
          this.vel += acc * h;
          this.cur += this.vel * h;
        }
      }

      const settled = Math.abs(this.cur - this.target) <= 0.0005 && Math.abs(this.vel) <= 0.0005;
      if (settled) {
        this.cur = this.target;
        this.vel = 0;
        if (!this.still) {
          this.still = true;
          this.classList.add('rw--still');
        }
      } else {
        if (this.still) {
          this.still = false;
          this.classList.remove('rw--still');
        }
      }

      this.render();

      if (!settled || this.dragging) {
        this.raf = requestAnimationFrame((ts) => this.frame(ts));
      } else {
        this.raf = 0;
        this.lastTime = 0;
      }
    }

    kick() {
      if (!this.raf) {
        this.raf = requestAnimationFrame((ts) => this.frame(ts));
      }
    }

    /* ----------------------------------------------------
       5. INDEX & ACTIVE LOOK NAVIGATION
       ---------------------------------------------------- */
    setIndex(i, silent = false) {
      const modIndex = ((i % this.n) + this.n) % this.n;
      if (modIndex === this.index && !silent) return;

      this.index = modIndex;

      // Progress bar ticks
      this.ticks.forEach((tick, idx) => {
        const isCurrent = idx === this.index;
        tick.setAttribute('aria-current', isCurrent ? 'true' : 'false');
        tick.classList.toggle('is-past', idx < this.index);
        tick.classList.toggle('is-run', isCurrent && this.playing);
      });

      // Panels swap
      this.panels.forEach((p, idx) => {
        p.hidden = idx !== this.index;
        p.classList.remove('is-in');
      });

      const activePanel = this.panels[this.index];
      if (activePanel) {
        activePanel.hidden = false;
        void activePanel.offsetWidth; // reflow to trigger animation
        activePanel.classList.add('is-in');
        const itemCount = activePanel.querySelectorAll('.rw__item').length;
        if (this.piecesLabel) {
          this.piecesLabel.textContent = `${itemCount} pieces`;
        }
      }

      // Active hero swap
      this.heroes.querySelectorAll('.rw__hero').forEach((h, idx) => {
        h.classList.toggle('is-on', idx === this.index);
        h.setAttribute('aria-hidden', idx === this.index ? 'false' : 'true');
      });

      // Announce look change to screen readers
      if (this.liveEl && !silent) {
        this.liveEl.textContent = `Look ${this.index + 1}: ${this.looks[this.index].name}`;
      }

      // Trigger light sweep band animation across models
      if (!silent && !this.reducedMotion) {
        this.stage.classList.remove('is-sweep');
        void this.stage.offsetWidth;
        this.stage.classList.add('is-sweep');
      }

      this.restartAutoplay();
    }

    moveTo(T) {
      this.target = T;
      this.setIndex(T);
      this.kick();
    }

    next() {
      this.moveTo(Math.round(this.target) + 1);
    }

    prev() {
      this.moveTo(Math.round(this.target) - 1);
    }

    go(lookIndex) {
      let delta = ((lookIndex - this.index) % this.n + this.n) % this.n;
      if (delta > this.n / 2) delta -= this.n;
      this.moveTo(Math.round(this.target) + delta);
    }

    /* ----------------------------------------------------
       6. 5s AUTOPLAY WITH TICK ANIMATION
       ---------------------------------------------------- */
    restartAutoplay() {
      clearTimeout(this.timer);
      this.classList.remove('is-playing');
      this.ticks.forEach(t => t.classList.remove('is-run'));

      if (!this.playing || this.engaged) return;

      void this.offsetWidth;
      this.classList.add('is-playing');
      const activeTick = this.ticks[this.index];
      if (activeTick) activeTick.classList.add('is-run');

      this.timer = setTimeout(() => {
        if (!document.hidden && !this.dragging && !this.panelHover && !this.engaged) {
          this.next();
        } else {
          this.restartAutoplay();
        }
      }, this.speed);
    }

    play(flag) {
      this.playing = flag;
      if (this.autoBtn) {
        this.autoBtn.setAttribute('aria-pressed', flag ? 'true' : 'false');
      }
      this.restartAutoplay();
    }

    engage() {
      this.engaged = true;
      this.play(false);
    }

    /* ----------------------------------------------------
       7. CONTROLS & INTERACTIVE LISTENERS
       ---------------------------------------------------- */
    initControls() {
      if (this.nextBtn) this.nextBtn.addEventListener('click', () => this.next());
      if (this.prevBtn) this.prevBtn.addEventListener('click', () => this.prev());

      if (this.autoBtn) {
        this.autoBtn.addEventListener('click', () => {
          if (!this.playing) this.engaged = false;
          this.play(!this.playing);
        });
      }

      this.ticks.forEach(t => {
        t.addEventListener('click', () => {
          this.go(parseInt(t.dataset.rwTick, 10));
        });
      });

      // Keyboard arrow navigation
      this.stage.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowRight') {
          e.preventDefault();
          this.next();
        } else if (e.key === 'ArrowLeft') {
          e.preventDefault();
          this.prev();
        }
      });

      // Horizontal trackpad wheel
      let wheelAcc = 0;
      let wheelLock = 0;
      this.stage.addEventListener('wheel', (e) => {
        if (Math.abs(e.deltaX) <= Math.abs(e.deltaY)) return;
        e.preventDefault();
        if (Date.now() < wheelLock) return;
        wheelAcc += e.deltaX;
        if (Math.abs(wheelAcc) > 45) {
          wheelAcc > 0 ? this.next() : this.prev();
          wheelAcc = 0;
          wheelLock = Date.now() + 520;
        }
      }, { passive: false });

      // Pause on panel mouse hover
      const panelCol = this.querySelector('.rw__panel');
      if (panelCol) {
        panelCol.addEventListener('pointerenter', (e) => {
          if (e.pointerType === 'mouse') this.panelHover = true;
        });
        panelCol.addEventListener('pointerleave', () => {
          this.panelHover = false;
          this.restartAutoplay();
        });
      }
    }

    /* ----------------------------------------------------
       8. POINTER DRAG & SWIPE PHYSICS
       ---------------------------------------------------- */
    initDrag() {
      this.stage.addEventListener('pointerdown', (e) => {
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        this.startX = e.clientX;
        this.startY = e.clientY;
        this.startTarget = this.target;
        this.pointerId = e.pointerId;
        this.samples = [{ x: e.clientX, t: performance.now() }];
      });

      this.stage.addEventListener('pointermove', (e) => {
        if (this.pointerId !== e.pointerId) return;
        const dx = e.clientX - this.startX;
        const dy = e.clientY - this.startY;

        if (!this.dragging) {
          if (Math.abs(dy) > 10 && Math.abs(dy) > Math.abs(dx)) {
            this.pointerId = null;
            return;
          }
          if (Math.abs(dx) > 8 && Math.abs(dx) > 1.2 * Math.abs(dy)) {
            this.dragging = true;
            this.stage.classList.add('is-drag');
            this.stage.setPointerCapture(this.pointerId);
          }
        }

        if (this.dragging) {
          this.samples.push({ x: e.clientX, t: performance.now() });
          this.samples = this.samples.slice(-6);
          this.target = this.startTarget - dx / (this.unit || 240);
          this.kick();
        }
      });

      const endDrag = (e) => {
        if (this.pointerId !== e.pointerId) return;
        this.pointerId = null;
        if (!this.dragging) return;

        this.dragging = false;
        this.stage.classList.remove('is-drag');
        this.suppressClick = Date.now() + 80;

        const a = this.samples[0];
        const b = this.samples[this.samples.length - 1];
        const dt = Math.max(1, b.t - a.t);
        const vx = (b.x - a.x) / dt;
        const from = Math.round(this.startTarget);

        let dest = Math.round(this.target - (vx * 160) / (this.unit || 240));
        if (dest === from && Math.abs(vx) > 0.3) {
          dest = from + (vx < 0 ? 1 : -1);
        }

        dest = Math.min(from + 2, Math.max(from - 2, dest));
        this.moveTo(dest);
      };

      this.stage.addEventListener('pointerup', endDrag);
      this.stage.addEventListener('pointercancel', endDrag);

      // Clicking background bodies moves them to front
      this.actors.addEventListener('click', (e) => {
        if (Date.now() < this.suppressClick) return;
        const hit = e.target.closest('.rw__hit');
        if (!hit) return;
        const a = parseInt(hit.dataset.rwHit, 10);
        let k = ((a - Math.round(this.target)) % this.N + this.N) % this.N;
        if (k > this.N / 2) k -= this.N;
        if (k !== 0 && Math.abs(k) < this.n) {
          this.moveTo(Math.round(this.target) + k);
        }
      });
    }

    /* ----------------------------------------------------
       9. CUSTOM DRAG / VIEW CURSOR
       ---------------------------------------------------- */
    initCursor() {
      if (!this.cursor) return;
      if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
        this.cursor.remove();
        return;
      }

      this.classList.add('rw--cursor');

      this.stage.addEventListener('pointerenter', (e) => {
        const rect = this.stage.getBoundingClientRect();
        this.cursorX = e.clientX - rect.left;
        this.cursorY = e.clientY - rect.top;
        this.targetCursorX = this.cursorX;
        this.targetCursorY = this.cursorY;
        this.cursor.classList.add('is-on');
        this.startCursorLoop();
      });

      this.stage.addEventListener('pointermove', (e) => {
        const rect = this.stage.getBoundingClientRect();
        this.targetCursorX = e.clientX - rect.left;
        this.targetCursorY = e.clientY - rect.top;

        // Check if hovering zoom or pins
        const target = e.target;
        const isZoom = target.closest('[data-rw-zoom]');
        const isPin = target.closest('.rw__pin') || target.closest('.rw__hit');

        this.cursor.classList.toggle('is-view', !!isZoom && !this.dragging);
        this.cursor.classList.toggle('is-link', !!isPin && !this.dragging);

        const label = this.cursor.querySelector('.rw__cursor-label');
        if (label) {
          label.textContent = isZoom ? 'VIEW' : 'DRAG';
        }
      });

      this.stage.addEventListener('pointerleave', () => {
        this.cursor.classList.remove('is-on', 'is-view', 'is-link');
      });
    }

    startCursorLoop() {
      if (this.cursorRaf) return;
      const step = () => {
        this.cursorX += (this.targetCursorX - this.cursorX) * 0.18;
        this.cursorY += (this.targetCursorY - this.cursorY) * 0.18;
        this.cursor.style.transform = `translate3d(${this.cursorX.toFixed(1)}px, ${this.cursorY.toFixed(1)}px, 0)`;

        if (this.cursor.classList.contains('is-on')) {
          this.cursorRaf = requestAnimationFrame(step);
        } else {
          this.cursorRaf = 0;
        }
      };
      this.cursorRaf = requestAnimationFrame(step);
    }

    /* ----------------------------------------------------
       10. VIEW LOOK LIGHTBOX POPUP & PINS
       ---------------------------------------------------- */
    initLightbox() {
      const zoomBtns = this.querySelectorAll('[data-rw-zoom]');
      const lbClose = document.getElementById('rw-lb-close');

      const openLb = () => {
        this.engage();
        if (!this.lightbox) return;
        const currentLook = this.looks[this.index];
        const lbImg = document.getElementById('rw-lb-img');
        const lbPinsContainer = document.getElementById('rw-lb-pins');

        if (lbImg) {
          lbImg.src = `/static/${currentLook.hd}`;
          lbImg.alt = currentLook.name;
        }

        // Render pins on popup lightbox
        if (lbPinsContainer) {
          lbPinsContainer.innerHTML = '';
          currentLook.items.forEach((item, idx) => {
            const pin = document.createElement('button');
            pin.className = 'rw__pin';
            pin.style.left = `${item.pin_x}%`;
            pin.style.top = `${item.pin_y}%`;
            pin.setAttribute('aria-label', `Piece ${idx + 1}: ${item.name}`);
            pin.innerHTML = `
              <span class="rw__pin-dot">${idx + 1}</span>
              <span class="rw__pin-tip">${item.name}</span>
            `;
            pin.addEventListener('click', (e) => {
              e.stopPropagation();
              this.hotlinkItem(idx + 1);
              closeLb();
            });
            lbPinsContainer.appendChild(pin);
          });
        }

        this.lightbox.classList.add('is-open');
        this.lightbox.hidden = false;
      };

      const closeLb = () => {
        if (!this.lightbox) return;
        this.lightbox.classList.remove('is-open');
        setTimeout(() => { this.lightbox.hidden = true; }, 300);
      };

      zoomBtns.forEach(btn => btn.addEventListener('click', openLb));
      if (lbClose) lbClose.addEventListener('click', closeLb);
      if (this.lightbox) {
        this.lightbox.addEventListener('click', (e) => {
          if (e.target === this.lightbox) closeLb();
        });
      }

      // Hotspot pin click in hero stage
      this.stage.addEventListener('click', (e) => {
        const pin = e.target.closest('.rw__pin');
        if (pin) {
          this.engage();
          const itemNum = parseInt(pin.dataset.pinOrder, 10);
          this.hotlinkItem(itemNum);
        }
      });
    }

    hotlinkItem(cardNum) {
      // Clear existing hot states
      this.querySelectorAll('.rw__item, .rw__pin').forEach(el => el.classList.remove('is-hot'));

      const activePanel = this.panels[this.index];
      if (!activePanel) return;

      const row = activePanel.querySelector(`[data-rw-card="${cardNum}"]`);
      const pin = this.stage.querySelector(`.rw__hero.is-on .rw__pin[data-pin-order="${cardNum}"]`);

      if (row) {
        row.classList.add('is-hot');
        row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      if (pin) pin.classList.add('is-hot');
    }

    /* ----------------------------------------------------
       11. REAL CART INTEGRATION & BUNDLE PURCHASE
       ---------------------------------------------------- */
    initCartActions() {
      // Single Item Add to Bag
      this.addEventListener('click', async (e) => {
        const addBtn = e.target.closest('[data-rw-add]');
        if (!addBtn) return;
        this.engage();

        const itemRow = addBtn.closest('.rw__item');
        const slug = itemRow.dataset.slug;
        const sizeSelect = itemRow.querySelector('.rw__size');
        const size = sizeSelect ? sizeSelect.value : '';

        addBtn.classList.add('is-loading');

        try {
          const resp = await fetch('/cart/add/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'X-Requested-With': 'fetch',
              'X-CSRFToken': this.csrf
            },
            body: new URLSearchParams({ slug, size, qty: 1 })
          });

          const data = await resp.json();
          addBtn.classList.remove('is-loading');

          if (resp.ok && data.ok) {
            addBtn.classList.add('is-added');
            window.showToast(data.message);
            window.updateCartBadge(data.count);
            window.openCartDrawer();
            setTimeout(() => addBtn.classList.remove('is-added'), 2200);
          } else {
            throw new Error(data.message || 'Could not add piece.');
          }
        } catch (err) {
          addBtn.classList.remove('is-loading');
          window.showToast(err.message || 'Error adding piece.');
        }
      });

      // Add Full Look to Bag (10% Bundle Discount)
      this.addEventListener('click', async (e) => {
        const allBtn = e.target.closest('[data-rw-all]');
        if (!allBtn) return;
        this.engage();

        const panel = allBtn.closest('.rw__look-panel');
        const lookId = panel.dataset.lookId;
        const params = new URLSearchParams({ look_id: lookId });

        panel.querySelectorAll('.rw__item').forEach(row => {
          const slug = row.dataset.slug;
          const sz = row.querySelector('.rw__size')?.value || '';
          params.append(`size_${slug}`, sz);
        });

        allBtn.disabled = true;
        allBtn.textContent = 'Adding Bundle...';

        try {
          const resp = await fetch('/cart/add-look/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
              'X-Requested-With': 'fetch',
              'X-CSRFToken': this.csrf
            },
            body: params
          });

          const data = await resp.json();
          allBtn.disabled = false;

          if (resp.ok && data.ok) {
            allBtn.classList.add('is-done');
            allBtn.textContent = '✓ Full Look in Bag (10% Saved)';
            window.showToast(data.message);
            window.updateCartBadge(data.count);
            window.openCartDrawer();
            setTimeout(() => {
              allBtn.classList.remove('is-done');
              allBtn.textContent = 'Add full look to bag →';
            }, 3000);
          } else {
            throw new Error(data.message || 'Failed to add bundle.');
          }
        } catch (err) {
          allBtn.disabled = false;
          allBtn.textContent = 'Add full look to bag →';
          window.showToast(err.message || 'Failed to add bundle.');
        }
      });
    }
  }

  // Register Custom Element
  if (!customElements.get('runway-section')) {
    customElements.define('runway-section', RunwaySection);
  }
})();
